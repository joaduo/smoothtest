# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import os
import re
import time
from .base import AutoTestBase
from collections import defaultdict
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

def realPath(path, retries=1, sleep=0.1):
    for _ in range(retries + 1):
        try:
            return os.path.realpath(path)
        except Exception as e:
            time.sleep(sleep)
    raise e

class FileAction(FileSystemEventHandler):
    '''

    '''
    def __init__(self, path, event_type=None):
        self._event_type = event_type
        self._path = path
        self._event_callbacks = defaultdict(list)

    def __call__(self, event, manager):
        '''
        The manager will call this object when an event is triggered.
        :param event: inotify event
        :param manager: inotify manager
        '''
        #watchdog works over directories
        #make sure this is the correct path
        if self.real_path != realPath(event.src_path):
            return
        self._call(event, manager)
        
    def _call(self, event, manager):
        #call all the callbacks associated with this file 
        for callback in self._event_callbacks[event.event_type]:
            callback(event, self, manager)

    def append(self, callback, event_type=None):
        '''
        Append new callback to the action's list of callbacks

        If you add callbacks to a registered action, you need to re-watch the
        action on the InotifyManager. (no need to remove)

        :param callback: callback to call when an inotify event matches the event_type
        :param event_type: event to be matched by the event on the path
        '''
        if event_type is None:
            assert self._event_type, ('You must provide a event_type or set a'
                                ' default event_type in PathAction initialization')
            event_type = self._event_type
        if callback not in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].append(callback)

    def remove(self, callback, event_type=None):
        '''
        Remove callback to the action's list of callbacks.
        If no event_type is specified, all (event_type, callback) associations will be
        removed.

        :param callback: callbact to call when an inotify event matches the event_type
        :param event_type: optional event_type when a specific (event_type, callback) pair wants
            to be removed
        '''

        if event_type == None:
            #no event_type, then remove callback from all lists
            for event_type,functions in self._event_callbacks.iteritems():
                if callback in functions:
                    functions.remove(callback)
        else:
            #remove callback for a specific event_type
            if event_type in self._event_callbacks:
                if callback in self._event_callbacks[event_type]:
                    self._event_callbacks[event_type].remove(callback)

    @property
    def real_path(self):
        return realPath(self._path)

    @property
    def path(self):
        return self._path
    
    @property
    def real_dir(self):
        return realPath(os.path.dirname(self._path))
        
    @property
    def event_types(self):
        return self._event_callbacks.keys()
    
    def on_moved(self, event):
        self.__call__(event, None)

    def on_created(self, event):
        self.__call__(event, None)

    def on_deleted(self, event):
        self.__call__(event, None)

    def on_modified(self, event):
        self.__call__(event, None)

class DirAction(FileAction):
    def __init__(self, path, path_filter=lambda x:True, event_type=None):
        self.path_filter = path_filter
        super(DirAction, self).__init__(path, event_type)
        
    def __call__(self, event, manager):
        if self.path_filter(realPath(event.src_path)):
            self._call(event, manager)


class SourceWatcher(AutoTestBase):
    def __init__(self):
        self._file_actions = {}
        self._dir_actions = {}
        self._observer = None

    def watch_file(self, path, callback):
        dir_path = realPath(os.path.dirname(path))

        def callback_wrapper(event, action, mnager):
            self.log.i(event)
            callback(path)
        
        action = self._file_actions.setdefault(path, FileAction(path))
        action.append(callback_wrapper, 'modified')
        #action.append(callback_wrapper, 'created')
        
    def start_observer(self):
        observer = Observer()
        for action in self._file_actions.values():
            #We need to watch directories since watchdog doesn't support files??
            observer.schedule(action, action.real_dir)

        for action in self._dir_actions.values():
            observer.schedule(action, action.real_dir, recursive=True)
        
        self._observer = observer
        self._observer.start()
        
    def unwatch_all(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
        self._file_actions.clear()
        self._dir_actions.clear()

    def watch_recursive(self, dir_path, callback, path_filter=None):
        path_filter = path_filter if path_filter else lambda x:True
        
        def callback_wrapper(event, action, mnager):
            callback(dir_path)
            
        if isinstance(path_filter, basestring):
            def _path_filter(path):
                return re.match(path_filter, path)
        else:
            assert callable(path_filter)
            _path_filter = path_filter

        action = self._dir_actions.setdefault(dir_path, DirAction(dir_path, _path_filter))
        action.append(callback_wrapper, 'modified')
        #action.append(callback_wrapper, 'created')

    def dispatch(self, timeout=0.0):
        pass

    def get_fd(self):
        return None

def smoke_test_module():
    sw = SourceWatcher()
    def callback(path):
        print 'Changed!', repr(path)
    path = __file__ + '.smoke_test_file'
    print path
    sw.watch_file(path, callback)
    sw.watch_file(__file__, callback)
    sw.watch_recursive(os.path.dirname(__file__), callback)
    print sw._file_actions,  sw._dir_actions
    sw.start_observer()
    import time
    sec = 3
    time.sleep(0.5)
    if os.path.exists(path):
        os.remove(path)
    with open(path,'w') as f:
        f.write('Hello World!')
    time.sleep(0.5)
    if os.path.exists(path):
        os.remove(path)
    time.sleep(sec)
    sw.unwatch_all()

if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
rel_imp.init()
import os
from .base import AutoTestBase
from collections import defaultdict
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time
from pprint import pformat


def realPath(path):
    return os.path.realpath(path)


class FileAction(FileSystemEventHandler):
    '''
    Handles incoming events from watchdog observer and calls the
    connected callback.
    Also helps filtering and avoids firing callbacks too often (given a threshold) 
    '''
    def __init__(self, path, event_type=None, time_threshold=1, log=None):
        self._event_type = event_type
        self._path = path
        self._event_callbacks = defaultdict(list)
        self._last_time = time.time()
        self._time_threshold = time_threshold
        self.log = log

    def __call__(self, event, manager):
        '''
        The manager will call this object when an event is triggered.
        :param event: inotify event
        :param manager: inotify manager
        '''
        # watchdog works over directories
        # make sure this is the correct path
        if self.real_path != realPath(event.src_path):
            return
        self._call(event, manager)

    def _enough_time(self):
        # Decides if enough time passed since the last event
        if not self._time_threshold:
            return True
        last = self._last_time
        now = self._last_time = time.time()
        return now - last > self._time_threshold

    def _call(self, event, manager):
        # Handle callback calling if enough time passed since last event
        if not self._enough_time():
            return
        # call all the callbacks associated with this file
        # Avoid calling 1 callback more than once per event
        called = set()
        for callback in self._event_callbacks[event.event_type]:
            if callback not in called:  # avoid calling twice
                self.log.d('Dispatching event for %r' % event)
                callback(event, self, manager)
                called.add(callback)

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

        if event_type is None:
            # no event_type, then remove callback from all lists
            for event_type, functions in self._event_callbacks.iteritems():
                if callback in functions:
                    functions.remove(callback)
        else:
            # remove callback for a specific event_type
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
    '''
    Does the same job as FileAction, but for directories 
    '''
    def __init__(self, path, path_filter=None, event_type=None, log=None):
        self.path_filter = path_filter
        super(DirAction, self).__init__(path, event_type, log=log)

    def __call__(self, event, manager):
        # The observer notifies all actions, we need to filter by path Dooh!
        real_path = realPath(event.src_path)
        if self.real_path != os.path.commonprefix([self.real_path, real_path]):
            return
        if not self.path_filter:
            self._call(event, manager)
        elif self.path_filter(realPath(event.src_path)):
            self._call(event, manager)


class SourceWatcher(AutoTestBase):
    '''
    Responsible of watching files and directories changes.
    It triggers callbacks passed for each of these paths.
    '''
    def __init__(self):
        self._file_actions = {} # Actions to be executed upon file changes events
        self._dir_actions = {} # Actions to be executed upon directory changes events
        self._observer = None # Watchdog observer instance

    def start_observer(self):
        '''
        Creates a watchdog Observer instances and starts it.
        Will connect watched files/dirs to respective actions for each file/dir.
        '''
        if not (self._file_actions or self._dir_actions):
            self.log.d('No files or dirs to watch')
            return
        # Get rid of previous watching and stop previous observer thread
        self.unwatch_all(clear=False)
        observer = Observer()
        # Connect file actions
        for action in self._file_actions.values():
            # We need to watch directories since watchdog doesn't support
            # files??
            observer.schedule(action, action.real_dir)
        # Connect dir actions
        for action in self._dir_actions.values():
            observer.schedule(action, action.real_dir, recursive=True)
        self.log.d('Starting observer for:\n  {files}\n  {dirs}'.
                   format(files=pformat(self._file_actions.keys()),
                          dirs=pformat(self._dir_actions.keys())))
        self._observer = observer
        # Start observer thread
        self._observer.start()

    def watch_file(self, path, callback):
        self.log.d('Watching file {path!r}'.format(path=path))

        def callback_wrapper(event, action, mnager):
            callback(path)

        action = self._file_actions.setdefault(path,
                                               FileAction(path, log=self.log))
        action.append(callback_wrapper, 'modified')

    def watch_recursive(self, path, callback, path_filter=None):
        dir_path = realPath(path)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # its a dir, need to wat recursively
            self._watch_dir(dir_path, callback, path_filter)
        else:
            # Its a file!
            self.watch_file(path, callback)

    def _watch_dir(self, dir_path, callback, path_filter):
        self.log.d('Recursive watching dir {dir_path!r}'
                   .format(dir_path=dir_path))

        def callback_wrapper(event, action, mnager):
            callback(dir_path)

        action = self._dir_actions.setdefault(
            dir_path,
            DirAction(
                dir_path,
                path_filter,
                log=self.log))
        action.append(callback_wrapper, 'modified')

    def unwatch_all(self, clear=False):
        if self._observer:
            self.log.d('Stopping observer for:\n  {files}\n  {dirs}'.
                       format(files=pformat(self._file_actions.keys()),
                              dirs=pformat(self._dir_actions.keys())))
            self._observer.stop()
            self._observer.join()
            self._observer = None
        if clear:
            self._file_actions.clear()
            self._dir_actions.clear()


def smoke_test_module():
    sw = SourceWatcher()

    def callback(path):
        print 'Changed!', repr(path)
    path = __file__ + '.smoke_test_file'
    print path
    sw.watch_file(path, callback)
    sw.watch_file(__file__, callback)
    sw.watch_recursive(os.path.dirname(__file__), callback)
    print sw._file_actions, sw._dir_actions
    sw.start_observer()
    sec = 0.05
    time.sleep(sec)
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'w') as f:
        f.write('Hello World!')
    time.sleep(sec)
    if os.path.exists(path):
        os.remove(path)
    time.sleep(sec)
    sw.unwatch_all()
    sw.start_observer()
    sw.unwatch_all()

if __name__ == "__main__":
    smoke_test_module()

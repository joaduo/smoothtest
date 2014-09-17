# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''

import os
from inotifyx import IN_CREATE, IN_DELETE_SELF, IN_MOVED_TO, IN_ALL_EVENTS
from smoothtest.autotest.path import pathExists, realPath, pathHead
from common.defaultdict import defaultdict
from smoothtest.autotest.base import AutoTestBase

class PathAction(AutoTestBase):
    '''
    For using the InotifyManager you need to pass PathAction instances to
    the watch and unregister classes.
    
    This is needed becase PathAction keeps tracks of the state of a file/dir
    in the case of deletion. So InotifyManager knows will watch it's parent
    dir for creation of the file.
    
    from inotifyx import  IN_ALL_EVENTS, IN_CREATE, IN_IGNORED, \
        IN_DELETE_SELF, IN_DELETE, IN_CLOSE_WRITE, IN_ATTRIB, IN_CLOSE, \
        IN_CLOSE_NOWRITE, IN_MOVED_TO

    '''
    def __init__(self, path, default_mask=0):
        self._default_mask = default_mask
        self._path = path
        self._watch_head = not os.path.exists(path)
        self._mask_callbacks = defaultdict(list)
        self.append(self._delete_callback, IN_DELETE_SELF)

    def __call__(self, event, manager):
        '''
        The manager will call this object when an event is triggered.
        :param event: inotify event
        :param manager: inotify manager
        '''
        if self._watch_head:
            self._path_head_callback(event, manager)
        else:
            for mask, callbacks in self._mask_callbacks.iteritems():
                if mask & event.mask:
                    self._run_callbacks(callbacks, event, manager)

    def _run_callbacks(self, functions, event, manager):
        for function in functions:
            function(event, self, manager)

    def _delete_callback(self, event, action, manager):
        self._watch_head = True
        manager.watch(self)

    def _path_head_callback(self, event, manager):
        '''
        If the watched dir/file is deleted or doesn't exist, we watch the parent
        dir (head) of the path.
        We need to create a callback for events on the parent's path. This
        method is the callback.
        
        :param event: event of the watched path
        :param manager: inotify manager instance watching the path 
        '''
        if event.mask & IN_DELETE_SELF:
            raise RuntimeError('Path head deleted. Can\'t keep watching it: %r'%self.path)
        if pathExists(self.real_path):
            self.log.debug('Path exists: %r'%self.real_path)
            #No longer watching the head folder
            self._watch_head = False
            #Now we watch the file egain (remove and readds)
            manager.watch(self)
            #Call this action to process the file events
            self.__call__(event, manager)
        else:
            self.log.debug('Path still doesn\'t exist: %r'%self.real_path)

    def append(self, callback, mask=None):
        '''
        Append new callback to the action's list of callbacks
        
        If you add callbacks to a registered action, you need to re-watch the
        action on the InotifyManager. (no need to remove)
        
        :param callback: callback to call when an inotify event matches the mask 
        :param mask: maks to be matched by the event on the path
        '''
        if mask is None:
            assert self._default_mask, ('You must provide a mask or set a'
                                ' default mask in PathAction initialization')
            mask = self._default_mask
        if callback not in self._mask_callbacks[mask]:
            self._mask_callbacks[mask].append(callback)

    def remove(self, callback, mask=None):
        '''
        Remove callback to the action's list of callbacks.
        If no mask is specified, all (mask, callback) associations will be
        removed.
        
        :param callback: callbact to call when an inotify event matches the mask 
        :param mask: optional mask when a specific (mask, callback) pair wants 
            to be removed
        '''
        
        if mask == None: 
            #no mask, then remove callback from all lists
            for mask,functions in self._mask_callbacks.iteritems():
                if callback in functions:
                    functions.remove(callback)
        else: 
            #remove callback for a specific mask
            if mask in self._mask_callbacks:
                if callback in self._mask_callbacks[mask]:
                    self._mask_callbacks[mask].remove(callback)

    @property
    def real_path(self):
        return realPath(self._path)

    @property
    def path(self):
        if self._watch_head:
            return pathHead(self.real_path)
        else:
            return self.real_path
    @property
    def mask(self):
        if self._watch_head:
            return IN_CREATE|IN_MOVED_TO#|IN_ALL_EVENTS
        else:
            return reduce(lambda x,y: x|y, self._mask_callbacks, 0)

def smoke_test_module():
    from smoothtest.autotest.InotifyManager import InotifyManager
    mngr = InotifyManager()
    action = PathAction(path='loren_ipsum.txt')
    
    callback = lambda ev, mngr: None
    action.append(callback, IN_CREATE)
    print action.path
    print action.real_path
    print mngr._mask_str(action.mask)
    
    action.remove(callback, mask=IN_CREATE)
    action.append(callback, IN_ALL_EVENTS)
    action.remove(callback)
    
    

if __name__ == "__main__":
    smoke_test_module()

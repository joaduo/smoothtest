# -*- coding: utf-8 -*-
'''
Mepinta
Copyright (c) 2011-2012, Joaquin G. Duo


from inotifyx import  IN_ALL_EVENTS, \
 IN_CREATE, IN_IGNORED, IN_CREATE, IN_DELETE_SELF, IN_DELETE, IN_CLOSE_WRITE, \
 IN_ATTRIB, IN_CLOSE, IN_CLOSE_NOWRITE, IN_MOVED_TO
'''

from inotifyx import init, add_watch, rm_watch, get_events, IN_ALL_EVENTS, \
 IN_CREATE, IN_IGNORED, IN_CREATE, IN_DELETE_SELF, IN_DELETE, IN_CLOSE_WRITE, \
 constants, IN_ATTRIB
from smoothtest.autotest.base import AutoTestBase

class InotifyManager(AutoTestBase):
    '''
    
    '''
    def __init__(self):
        self.__wd_action = {}
        self._post_callbacks = []
        self.skip_post_callbacks = False
        self._fd = None

    @property
    def fd(self):
        if self._fd is None:
            self._fd = init()
        return self._fd

    def get_wd_action(self):
        return dict(self.__wd_action)

    def _mask_str(self, mask):
        flags_list = []
        for name, value in constants.iteritems():
            if value & mask and name != 'IN_ALL_EVENTS':
                flags_list.append(name)
        return '|'.join(flags_list)

    def _watch_path(self, path, mask):
        self.log.debug('Adding for fd:%s with flags:%s and path:%s' % (self.fd, self._mask_str(mask), path))
        wd = add_watch(self.fd, path, mask)
        self.log.debug('Sucessfully added with wd:%s' % wd)
        return wd

    def _remove_wd(self, wd):
        self.log.debug('Removing wd:%s from fd:%s' % (wd, self.fd))
        try:
            rm_watch(self.fd, wd)
        except IOError as error:
            self.log.debug('Ignoring rm_watch IOError %s' % error)
            pass

    def append_post_callback(self, callback):
        if callback in self._post_callbacks:
            raise RuntimeError('Function %r already in post events functions' % callback)
        self._post_callbacks.append(callback)

    def remove_post_callback(self, callback):
        if callback in self._post_callbacks:
            self._post_callbacks.remove(callback)

    def register(self, action):
        self.unregister(action)
        self._add_action(action)

    def unregister(self, action):
        action_wd = self.get_wd_action()
        if action in action_wd:
            wd = action_wd[action]
            self._remove_wd(wd)
            del self.__wd_action[wd]

    def _add_action(self, action):
        wd = self._watch_path(action.path, action.mask)
        self.__wd_action[wd] = action

    def _get_events(self, timeout):
        if timeout == None:
            events = get_events(self.fd)
        else:
            events = get_events(self.fd, timeout)
        return events

    def dispatch(self, timeout=0.0):
        events = self._get_events(timeout)
        for event in events:
            if event.wd in self.__wd_action:
                self.log.debug('Got event %s ' % event)
                action = self.__wd_action[event.wd]
                action(event, manager=self)
            elif event.mask & IN_IGNORED:
                self.log.debug('Ignored remove watch event %s' % event)
            else:
                self.log.warning('Unhandled event %s' % event)
        #If there was an event, then run the post functions
        self._run_post_callbacks(len(events))
        return len(events)

    def _run_post_callbacks(self, events_count):
        if not self.skip_post_callbacks and events_count:
            for function in self._post_callbacks:
                function(manager=self)
        else:
            #Next time won't skip them
            self.skip_post_callbacks = False

    def block_listening(self, timeout=None):
        #check that the manager won't block
        if not timeout and not len(self.__wd_action):
            raise RuntimeWarning('There is no event to listening to.')
        self.log.debug('Listening file events.')
        while len(self.__wd_action) > 0:
            self.dispatch(timeout)

if __name__ == '__main__':
#    from common.inotify.actions.PathAction import PathAction
    pass
#    def actionFunction(event, action, manager):
#        action.log('Event: %s' % event)
#
#    path = '/home/jduo/output'
#    action = PathAction(context, path=path, mask=IN_ALL_EVENTS)
#    action.appendFunction(actionFunction)
#    manager.register(action)
#    manager.block_listening()

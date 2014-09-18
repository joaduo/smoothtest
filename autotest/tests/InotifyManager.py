# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju Inc.
Copyright (c) 2011-2013, Joaquin G. Duo
'''
import unittest
from smoothtest.autotest.PathAction import PathAction
from smoothtest.autotest.InotifyManager import InotifyManager
from inotifyx import IN_ALL_EVENTS, IN_DELETE_SELF
import os

class InotifyManagerTest(unittest.TestCase):
    _example_file = 'watch_example_file.txt'
    _head_example_file = 'watch_head_example_file.txt'
    def tearDown(self):
        for name in [self._example_file, self._head_example_file]:
            if os.path.exists(name):
                os.remove(name)

    def _build_action_callback(self, name, log_list):
        #Test callback on delete event
        def action_callback(event, action, manager):
            self.assertIsInstance(action, PathAction)
            self.assertIsInstance(manager, InotifyManager)
            #action.log.i('{name}: {event}'.format(name=name, event=event))
            log_list.append('{name}: {event}'.format(name=name, event=event))
        return action_callback

    def _build_post_callback(self, name, log_list):
        def post_callback(manager):
            self.assertIsInstance(manager, InotifyManager)
            #manager.log.i('{name} Post Callback'.format(name=name))
            log_list.append('{name} POST_CALLBACK'.format(name=name))
        return post_callback

    def _pprint(self, obj):
        from pprint import pprint
        pprint(obj)

    def _create_file(self, path,  content='Example content'):
        assert not os.path.exists(path), 'File shouldn\'t exist: %r'%path
        with open(path, 'w') as f:
            if content:
                f.write(content)

    def test_watch(self):
        mngr = InotifyManager()
        path = 'watched_file.txt'
        action = PathAction(path)

        log_list = []

        delete_callback = self._build_action_callback('delete', log_list)
        action.append(delete_callback, mask=IN_DELETE_SELF)

        all_callback = self._build_action_callback('all', log_list)
        action.append(all_callback, mask=IN_ALL_EVENTS)

        mngr.watch(action)

        post_callback = self._build_post_callback('General', log_list)
        mngr.append_post_callback(post_callback)

        self._create_file(path)

        mngr.dispatch(timeout=1)

        os.remove(path)

        mngr.dispatch(timeout=1)

        #self._pprint(log_list)

        expected_log = ['all: 1: IN_CREATE|IN_ALL_EVENTS',
                         'General POST_CALLBACK',
                         'all: 2: IN_ALL_EVENTS|IN_ATTRIB',
                         'delete: 2: IN_ALL_EVENTS|IN_DELETE_SELF',
                         'all: 2: IN_ALL_EVENTS|IN_DELETE_SELF',
                         'General POST_CALLBACK']

        self.assertEqual(log_list, expected_log)

    def test_watch_head(self):
        mngr = InotifyManager()
        path = 'watched_file_head.txt'
        action = PathAction(path)

        log_list = []

        all_callback = self._build_action_callback('all', log_list)
        action.append(all_callback, mask=IN_ALL_EVENTS)
        mngr.watch(action)

        self._create_file(path)

        mngr.dispatch(timeout=1)

        os.remove(path)

        mngr.dispatch(timeout=1)

        self._create_file(path)

        mngr.dispatch(timeout=1)

        os.remove(path)

        mngr.dispatch(timeout=1)

        #self._pprint(log_list)

        expected_log = ['all: 1: IN_CREATE|IN_ALL_EVENTS',
                         'all: 2: IN_ALL_EVENTS|IN_ATTRIB',
                         'all: 2: IN_ALL_EVENTS|IN_DELETE_SELF',
                         'all: 1: IN_CREATE|IN_ALL_EVENTS',
                         'all: 3: IN_ALL_EVENTS|IN_ATTRIB',
                         'all: 3: IN_ALL_EVENTS|IN_DELETE_SELF']

        self.assertEquals(log_list, expected_log)


if __name__ == '__main__':
    unittest.main()

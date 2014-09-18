# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.base import AutoTestBase
from inotifyx import IN_CLOSE_WRITE
import os
from smoothtest.autotest.InotifyManager import InotifyManager
from smoothtest.autotest.PathAction import PathAction

class SourceWatcher(AutoTestBase):
    def __init__(self):
        #TODO!
        self._mask = IN_CLOSE_WRITE
        self._imngr = InotifyManager()
        self._file_action = {}
        self._dir_actions = {}

    def watch_file(self, path, callback):
        assert path not in self._file_action

        def callback_wrapper(event, action, mnager):
            self.log.i(event)
            callback(path)

        action = PathAction(path, self._mask)
        action.append(callback_wrapper)

        self._imngr.watch(action)

        self._file_action[path] = action

    def dispatch(self, timeout=0.0):
        self._imngr.dispatch(timeout)

    def watch_recursive(self, dir_path, regex='.*\.py'):
        msg = 'For recursive watching {dir_path} must the directory.'.format(dir_path=dir_path)
        assert os.path.isdir(dir_path), msg


    def unwatch_file(self, path):
        pass

    def get_fd(self):
        return self._imngr.fd

    def _watch_recursively(self, path):
        pass

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()

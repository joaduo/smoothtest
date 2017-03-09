# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
import rel_imp; rel_imp.init()
import re
import os
import logging
import traceback
from xpathwebdriver.base import is_valid_file, module_regex, CommandMixin
from .Logger import Logger
from .settings.solve_settings import solve_settings, register_settings
from .TestResults import TestException


class SmoothTestBase(object):
    log = Logger('autotest root', color=solve_settings().get('log_color'))

    @property
    def global_settings(self):
        return solve_settings()

    def _path_to_modstr(self, tst):
        tst = tst.replace(os.path.sep, '.')
        tst = re.sub(r'\.(pyc)|(py)$', '', tst).strip('.')
        return tst

    def split_test_path(self, test_path, meth=False):
        test_path = test_path.split('.')
        if meth:
            offset = -2
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            method = test_path[offset + 1]
            return module, class_, method
        else:  # only module+class
            offset = -1
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            return module, class_

    def get_module_file(self, module):
        pth = module.__file__
        if pth.endswith('.pyc'):
            pth = pth[:-1]
        return pth

    def reprex(self, e, print_=True):
        # TODO: shuoldn't format last exception,but passed one
        if print_:
            traceback.print_exc()
        return TestException(str(e), repr(e), traceback.format_exc())


def is_file_or_dir(path):
    '''
    Validate if a passed argument is a existing file (used by argsparse)
    '''
    # TODO: should it always validate module string?
    abspath = os.path.abspath(path)
    if not (os.path.exists(abspath)
            and (os.path.isfile(abspath) or os.path.isdir(abspath))
            or module_regex.match(path)
            ):
        logging.warn('File or dir %r does not exist.' % path)
    return path


class CommandBase(SmoothTestBase, CommandMixin):
    pass


class TestRunnerBase(object):

    def __init_values(self):
        if not hasattr(self, '_already_setup'):
            self._already_setup = {}

    def _setup_process(self, test, test_path, argv):
        self.__init_values()
        if (hasattr(test, 'setUpProcess')
                and test_path not in self._already_setup):
            test.setUpProcess(argv)
            self._already_setup[test_path] = (test, argv)

    def _tear_down_process(self):
        self.__init_values()
        for test, argv in self._already_setup.values():
            if hasattr(test, 'tearDownProcess'):
                self.log.d('Tearing down process for %r' % test)
                test.tearDownProcess(argv)
        self._already_setup.clear()


def smoke_test_module():
    s = SmoothTestBase()
    s.log.i(__file__)
    trb = TestRunnerBase()
    trb._setup_process(None, 'path.to.test', [])
    trb._tear_down_process()


if __name__ == "__main__":
    smoke_test_module()

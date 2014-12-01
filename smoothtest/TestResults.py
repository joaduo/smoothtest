# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from pprint import pformat
from collections import namedtuple
from smoothtest.utils import is_pickable


TestException = namedtuple('TestException', 'msg repr traceback')


class SmoothTestResult(object):
    def __init__(self, unittest_result):
        self._attrs = self.to_pickable_result(unittest_result)

    def __getattr__(self, name):
        attrs = super(SmoothTestResult, self).__getattribute__('_attrs')
        if name in attrs:
            return attrs[name]
        raise AttributeError('No attribute {name} in {self}'.format(**locals()))

    def __repr__(self):
        name = self.__class__.__name__
        run = 'run=%s' % self.testsRun
        errors = 'errors=%s' % len(self.errors)
        failures = 'failures=%s' % len(self.failures)
        return '<{name} {run} {errors} {failures}>'.format(**locals())

    def to_pickable_result(self, result):
        # Dictionary with example data
        accepted_attrs = {
                '_mirrorOutput': 'False',
                '_moduleSetUpFailed': 'False',
                #'_original_stderr': "<open file '<stderr>', mode 'w' at 0x7fe301fd61e0>",
                #'_original_stdout': "<open file '<stdout>', mode 'w' at 0x7fe301fd6150>",
                #'_previousTestClass': "<class '__main__.Example'>",
                #'_stderr_buffer': 'None',
                #'_stdout_buffer': 'None',
                '_testRunEntered': 'False',
                'buffer': 'False',
                'descriptions': 'True',
                'dots': 'True',
                'errors': [('__main__.Example.test_error',
                            'Traceback (most recent call last):\n  File "/home/jduo/000-JujuUnencrypted/EclipseProjects/smoothtest/testing_results.py", line 19, in test_error\n    raise LookupError(\'Purposely uncaught raised error!\')\nLookupError: Purposely uncaught raised error!\n')],
                'expectedFailures': [],
                'failfast': 'False',
                'failures': [('__main__.Example.test_failure',
                              'Traceback (most recent call last):\n  File "/home/jduo/000-JujuUnencrypted/EclipseProjects/smoothtest/testing_results.py", line 22, in test_failure\n    self.assertTrue(False, \'Forced failed Assert!\')\nAssertionError: Forced failed Assert!\n')],
                'shouldStop': 'False',
                'showAll': 'False',
                'skipped': [],
                #'stream': '<unittest.runner._WritelnDecorator object at 0x7fe301e5a550>',
                'testsRun': '3',
                'unexpectedSuccesses': [],
                }
        new_res = {}
        for name, val in result.__dict__.iteritems():
            if name not in accepted_attrs:
                continue
            if not is_pickable(val):
                if isinstance(val, list):
                    val = self.to_pickable_list(val)
                else:
                    val = repr(val)
            new_res[name] = val
        return new_res

    def to_pickable_list(self, lst):
        try:
            return [(self.to_pickable_test(test), msg) for test, msg in lst]
        except:
            return repr(lst)

    def to_pickable_test(self, test_case):
        if hasattr(test_case, 'test_path'):
            return test_case.test_path
        # By now we will simply replace the test case by its test_path
        mod_ = test_case.__class__.__module__
        class_ = test_case.__class__.__name__
        meth = test_case._testMethodName
        return '%s.%s.%s' % (mod_, class_, meth)


class TestResults(object):
    def __init__(self):
        self._results = []

    def append_exception(self, test_path, exn):
        self._results.append(('exception', test_path, exn))

    def append_unittest(self, test_path, result):
        self._results.append(('unittest_result', test_path, result))

    def append_results(self, results):
        self._results += results._results

    def __str__(self):
        return pformat(self._results)


def smoke_test_module():
    import pickle
    from smoothtest.Logger import Logger
    log = Logger(__name__)
    results = TestResults()
    pickle.dumps(results)
    str(results)
    results.append_exception('test_path', 'exn')
    results.failures = [('bla',2)]
    results.errors = [('bla',2)]
    results.total = [('bla',2)]
    log.i(str(results))


if __name__ == "__main__":
    smoke_test_module()

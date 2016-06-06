# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from collections import namedtuple
from .utils import is_pickable


TestException = namedtuple('TestException', 'msg repr traceback')


class SmoothTestResult(object):

    def __init__(self, unittest_result):
        self._attrs = self.to_pickable_result(unittest_result)

    def __getattr__(self, name):
        attrs = super(SmoothTestResult, self).__getattribute__('_attrs')
        if name in attrs:
            return attrs[name]
        raise AttributeError(
            'No attribute {name} in {self}'.format(**locals()))

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
                            'Traceback (most recent call last):\n  File "./smoothtest/testing_results.py", line 19, in test_error\n    raise LookupError(\'Purposely uncaught raised error!\')\nLookupError: Purposely uncaught raised error!\n')],
            'expectedFailures': [],
            'failfast': 'False',
            'failures': [('__main__.Example.test_failure',
                          'Traceback (most recent call last):\n  File "./smoothtest/testing_results.py", line 22, in test_failure\n    self.assertTrue(False, \'Forced failed Assert!\')\nAssertionError: Forced failed Assert!\n')],
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

    def _append_exception(self, test_path, exn):
        self._results.append(('exception', test_path, exn))

    def _append_unittest(self, test_path, result):
        if not isinstance(result, SmoothTestResult):
            result = SmoothTestResult(result)
        self._results.append(('unittest_result', test_path, result))

    def append_result(self, test_path, result):
        if isinstance(result, TestException):
            self._append_exception(test_path, result)
        else:
            self._append_unittest(test_path, result)

    def append_results(self, results):
        self._results += results._results

    def filter_results(self, result_type='unittest_result'):
        for rtype, test_path, result in self._results:
            if rtype == result_type:
                yield test_path, result

    def get_details(self, detail_type='errors'):
        for _, result in self.filter_results('unittest_result'):
            for method_path, _ in getattr(result, detail_type):
                yield method_path

    def get_total(self):
        results = self.filter_results('unittest_result')
        return sum(result.testsRun for _, result in results)

    def _get_counters(self, exceptions, failures, errors):
        total = self.get_total() + len(exceptions)
        counters = ('EXCEPTIONS={exceptions} FAILURES={failures} '
                    'ERRORS={errors} from TOTAL={total}'
                    .format(exceptions=len(exceptions),
                            failures=len(failures),
                            errors=len(errors),
                            total=total))
        return counters

    def get_detail_dict(self):
        detail_dict = dict(
            exceptions=list(
                tpath for tpath, _ in self.filter_results('exception')),
            failures=list(self.get_details('failures')),
            errors=list(self.get_details('errors')),
        )
        return detail_dict

    def __str__(self):
        return self._get_counters(**self.get_detail_dict())

    def get_return_value(self):
        details = lambda detail_type: list(self.get_details(detail_type))
        return int(bool(details('failures') or details('errors')))


def smoke_test_module():
    import pickle
    from smoothtest.Logger import Logger
    log = Logger(__name__)
    results = TestResults()
    pickle.dumps(results)
    str(results)
    results._append_exception('test_path', 'exn')
    results.failures = [('bla', 2)]
    results.errors = [('bla', 2)]
    results.total = [('bla', 2)]
    log.i(str(results))


if __name__ == "__main__":
    smoke_test_module()

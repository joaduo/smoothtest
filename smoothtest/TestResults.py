# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''


class TestResults(object):
    def __init__(self):
        self.total = []
        self.failures = []
        self.errors = []
        self.exceptions = []

    def append_exception(self, test_path, exn):
        self.exceptions.append((test_path, exn))

    def append_unittest(self, test_path, result):
        if result.errors:
            self.errors.append((test_path, len(result.errors)))
        if result.failures:
            self.failures.append((test_path, len(result.failures)))
        self.total.append((test_path, result.testsRun))

    def append_results(self, results):
        for name in 'total failures errors'.split():
            both = getattr(self, name) + getattr(results, name)
            setattr(self, name, both)

    def __str__(self):
        sum_func = lambda x,y: x + y[1]
        if self.failures or self.errors or self.exceptions:
            def str_detail(name, count, list_):
                cap = name.upper()
                str_ = '{cap}={count} '.format(**locals()) if count else ''
                detail = '\n  {name}:{list_}'.format(**locals()) if count else ''
                return str_, detail
            summary = ''
            details = ''
            for name, list_ in [('Errors', self.errors),
                                ('Exceptions', self.exceptions),
                                ('Failures', self.failures),
                                ('Total', self.total)]:
                if list_:
                    if name != 'Exceptions':
                        count = reduce(sum_func, list_, 0)
                    else:
                        count = len(list_)
                    str_, detail = str_detail(name, count, list_)
                    summary += str_
                    if name != 'Total':
                        details += detail
            details = '\nDetails:' + details if details else ''
            results_str = summary + details
        else:
            t = reduce(sum_func, self.total, 0)
            results_str = 'All {t} tests OK'.format(t=t)
        return results_str


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

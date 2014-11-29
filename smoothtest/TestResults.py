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

#    def _collect_stats(self, ans):
#        exceptions = errored = failed = total = 0
#        exlist = []
#        errlist = []
#        faillist = []
#        for tst_pth, result in ans.result:
#            if isinstance(result, TestException):
#                #exception running test
#                exceptions += 1
#                total += 1
#                exlist.append(tst_pth)
#                continue
#            #TestResult with failures or errors
#            result.errors and errlist.append(tst_pth)
#            result.failures and faillist.append(tst_pth)
#            errored += len(result.errors)
#            failed += len(result.failures)
#            total += result.testsRun
#        if not (failed or errored or exceptions):
#            msg = '\n  All %s OK' % total
#        else:
#            msg = ('\n  EXCEPT:{exceptions} FAILED:{failed} ERROR:{errored}'
#                   ' TOTAL:{total}'.format(**locals()))
#        for typ, lst in [('exceptions', exlist), ('errors', errlist),
#                         ('failures', faillist)]:
#            if lst:
#                msg += '\n    with %s: %s' % (typ, lst)
#        return msg

    def pickle(self):
        pass
#        errors = [repr(e) for e in result.errors]
#        failures = [repr(f) for f in result.failures]
#        return TestResult(result.testsRun, errors, failures)


def smoke_test_module():
    import pickle
    pickle.dumps(TestResults())


if __name__ == "__main__":
    smoke_test_module()

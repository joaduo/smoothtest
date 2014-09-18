# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger

class AutoTestBase(object):
    log = Logger('at')

    _kill_command = 'raise SystemExit'
    _kill_answer = 'doing SystemExit'
    def _dispatch_cmds(self, io_api):
        msg = io_api.recv()
        answer = []
        for params in msg:
            cmd, args, kwargs = params
            if cmd == self._kill_command:
                io_api.send(self._kill_answer)
                io_api.close()
                raise SystemExit(*args, **kwargs)
            try:
                result = getattr(self, cmd)(*args, **kwargs)
                answer.append((result, None))
            except Exception as e:
                answer.append((None, self.reprex(e)))
        io_api.send(answer)
        return answer


def smoke_test_module():
    base = AutoTestBase()
    base.log.d('Debug')
    base.log.i('Info')

if __name__ == "__main__":
    smoke_test_module()

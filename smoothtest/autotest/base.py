# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
import rel_imp; rel_imp.init()
from ..base import SmoothTestBase


class AutoTestBase(SmoothTestBase):
    def cmd(self, cmd, *args, **kwargs):
        #Make it ready for sending
        return [self._cmd(cmd, *args, **kwargs)]
    
    def _cmd(self, cmd, *args, **kwargs):
        #use when queying several commands
        return (cmd, args, kwargs)

    _kill_command = 'raise SystemExit'
    _kill_answer = 'doing SystemExit'
    def _dispatch_cmds(self, io_conn, duplex=True):
        msg = io_conn.recv()
        answer = []
        for params in msg:
            cmd, args, kwargs = params
            if cmd == self._kill_command:
                self.log.d('Killing myself...')
                self._receive_kill(*args, **kwargs)
                duplex and io_conn.send(self._kill_answer)
                io_conn.close()
                raise SystemExit(0)
            try:
                result = getattr(self, cmd)(*args, **kwargs)
                answer.append((result, None))
            except Exception as e:
                answer.append((None, self.reprex(e)))
        duplex and io_conn.send(answer)
        return answer
    
    def _receive_kill(self, *args, **kwargs):
        pass
    
    def split_test_path(self, test_path, meth=False):
        test_path = test_path.split('.')
        if meth:
            offset = -2
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            method = test_path[offset+1]
            return module, class_, method
        else: #only module+class
            offset = -1
            module = '.'.join(test_path[:offset])
            class_ = test_path[offset]
            return module, class_


def smoke_test_module():
    base = AutoTestBase()
    base.log.d('Debug')
    base.log.i('Info')
    test_path = 'smoothtest.tests.example.Example.Example.test_example'
    base.log.i(base.split_test_path(test_path))
    base.log.i(base.split_test_path(test_path, meth=True))


if __name__ == "__main__":
    smoke_test_module()

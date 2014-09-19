# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
from smoothtest.Logger import Logger

class AutoTestBase(object):
    log = Logger('at')
    
    def cmd(self, cmd, *args, **kwargs):
        #Make it ready for sending
        return [self._cmd(cmd)]
    
    def _cmd(self, cmd, *args, **kwargs):
        #use when queying several commands
        return (cmd, args, kwargs)

    _kill_command = 'raise SystemExit'
    _kill_answer = 'doing SystemExit'
    def _dispatch_cmds(self, io_pipe, handler=None, *largs, **lkwargs):
        msg = io_pipe.recv()
        answer = []
        for params in msg:
            cmd, args, kwargs = params
            if cmd == self._kill_command:
                self._receive_kill(*args, **kwargs)
                io_pipe.send(self._kill_answer)
                io_pipe.close()
                raise SystemExit(0)
            try:
                if hasattr(self, cmd) or not handler:
                    #raise exception if no handler and no attr
                    result = getattr(self, cmd)(*args, **kwargs)
                else:
                    result = handler(params, *largs, **lkwargs)
                answer.append((result, None))
            except Exception as e:
                answer.append((None, self.reprex(e)))
        io_pipe.send(answer)
        return answer
    
    def reprex(self, e):
        return repr(e)
    
    def _receive_kill(self, *args, **kwargs):
        pass


def smoke_test_module():
    base = AutoTestBase()
    base.log.d('Debug')
    base.log.i('Info')

if __name__ == "__main__":
    smoke_test_module()

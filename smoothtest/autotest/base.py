# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
import rel_imp; rel_imp.init()
from ..base import SmoothTestBase
from collections import namedtuple

cmd_fields = 'cmd args kwargs'
AutotestCmd = namedtuple('AutotestCmd', cmd_fields)
AutotestAnswer = namedtuple('AutotestAnswer', 'sent_cmd result error')

class AutoTestBase(SmoothTestBase):
    def cmd(self, cmd, *args, **kwargs):
        #Make it ready for sending
        cmd = [self._cmd(cmd, *args, **kwargs)]
        self.log.d('Packing cmd={cmd}'.format(cmd=cmd))
        return cmd
    
    def _cmd(self, cmd, *args, **kwargs):
        #use when queying several commands
        return AutotestCmd(cmd, args, kwargs)

    _kill_command = 'raise SystemExit'
    _kill_answer = 'doing SystemExit'
    def _dispatch_cmds(self, io_conn, duplex=True):
        commands = io_conn.recv()
        send = lambda msg: duplex and io_conn.send(msg)
        answers = []
        for cmd in commands:
            self.log.d('Receiving command: {cmd!r}'.format(cmd=cmd))
            if cmd.cmd == self._kill_command:
                self.log.d('Start killing myself...')
                self._receive_kill(*cmd.args, **cmd.kwargs)
                answers.append(AutotestAnswer(cmd, self._kill_answer, None))
                send(answers)
                io_conn.close()
                raise SystemExit(0)
            result = error = None
            try:
                result = getattr(self, cmd.cmd)(*cmd.args, **cmd.kwargs)
            except Exception as e:
                error = self.reprex(e)
            answers.append(AutotestAnswer(cmd, result, error))
        self.log.d('Answering {answers}'.format(answers=answers))
        send(answers)
        return answers
    
    def _receive_kill(self, *args, **kwargs):
        pass
    
    def fmt_answers(self, msg):
        output = ''
        for ans in msg:
            output += str(self._fmt_answer(ans))
        return output
    
    def _fmt_answer(self, answer):
        return 'cmd:%s result: %r, errors: %s\n' % (answer.sent_cmd.cmd, 
                                                 answer.result, answer.error)

    def _get_answer(self, answers, cmd):
        for ans in answers:
            if ans.sent_cmd.cmd == cmd:
                return ans
    
    def _kill_subprocess(self, block=False, timeout=None):
        self.log.d('Killing Slave child with pid %r.' % self._subprocess.ident)
        answer = None
        def end():
            self._subprocess.join()
            self._suprocess = None
            self._subprocess_conn.close()
            self._subprocess_conn = None
            
        if not self._subprocess:
            return answer
        
        if not self._subprocess.is_alive():
            self.log.w('Child terminated by himself.'
                       ' Exitcode:' % self._subprocess.exitcode)
            end()
        
        self._subprocess_conn.send(self.cmd(self._kill_command))

        if not block:
            return answer
        
        if self._subprocess_conn.poll(timeout):
            answer = self._subprocess_conn.recv()
            answer = self._get_answer(answer, self._kill_command)
            assert answer, 'No answer for the kill command sent.'
            self.log.d('Received kill answer %s' % self._fmt_answer(answer))
            pid, status = self._subprocess.ident, self._subprocess.exitcode
            self.log.i('Child with pid {pid} gently terminated with exit '
                       'status {status}.'.format(pid=pid, status=status))
        else:
            self._subprocess.terminate()
            pid, status = self._subprocess.ident, self._subprocess.exitcode
            self.log.w('Child pid {pid} killed by force with exit status {status}.'
                       ''.format(pid=pid, status=status))
        end()
        return answer

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


class ParentChildBase(object):
    pass

def smoke_test_module():
    base = AutoTestBase()
    print base.cmd(base.split_test_path)
    base.log.d('Debug')
    base.log.i('Info')
    test_path = 'smoothtest.tests.example.Example.Example.test_example'
    base.log.i(base.split_test_path(test_path))
    base.log.i(base.split_test_path(test_path, meth=True))


if __name__ == "__main__":
    smoke_test_module()

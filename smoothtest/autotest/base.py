# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
import rel_imp; rel_imp.init()
from ..base import SmoothTestBase
from collections import namedtuple
import multiprocessing
from types import MethodType, FunctionType
import sys

cmd_fields = 'cmd args kwargs'
AutotestCmd = namedtuple('AutotestCmd', cmd_fields)
AutotestAnswer = namedtuple('AutotestAnswer', 'sent_cmd result error')

class AutoTestBase(SmoothTestBase):
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


class ChildBase(AutoTestBase):
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

    def _get_cmd_str(self, cmd):
        if isinstance(cmd, MethodType):
            cmd = cmd.im_func.func_name
        if isinstance(cmd, FunctionType):
            cmd = cmd.func_name
        return cmd

    def cmd(self, cmd, *args, **kwargs):
        #Make it ready for sending        
        return [self._cmd(self._get_cmd_str(cmd), *args, **kwargs)]
    
    def _cmd(self, cmd, *args, **kwargs):
        #use when queying several commands
        return AutotestCmd(cmd, args, kwargs)


class TargetFunction(SmoothTestBase):
    def __init__(self, callback, parent, child, pre):
        self.callback = callback
        self.parent = parent
        self.child = child
        self.pre = pre
    
    def __call__(self):
        self.parent.close()
        sys.stdin.close()
        self.log.set_pre_post(pre=self.pre)
        self.log.d('Forked process started...')
        self.callback(self.child)


class ParentBase(ChildBase):
    def start_subprocess(self, callback, pre=''):
        parent, child = multiprocessing.Pipe()
        #Add space if defined
        pre = pre if not pre else pre + ' '
        #Windows needs target to be pickable
        target = TargetFunction(callback, parent, child, pre)
        
        self._subprocess = multiprocessing.Process(target=target)
        self._subprocess.start()
        self._subprocess_conn = parent
        child.close()

    def restart_subprocess(self, callback):
        self.kill(block=True, timeout=self._timeout)
        self.start_subprocess(callback)

    def kill(self, block=False, timeout=None):
        return self._kill_subprocess(block, timeout)
    
    def send(self, cmd, *args, **kwargs):
        self._subprocess_conn.send(self.cmd(cmd, *args, **kwargs))
        
    def recv(self):
        return self._subprocess_conn.recv()

    def poll(self):
        return self._subprocess_conn.poll()
    
    def fmt_answers(self, msg):
        output = ''
        for ans in msg:
            output += str(self._fmt_answer(ans)) + '\n'
        return output
    
    def _fmt_answer(self, answer):
        return 'cmd:%s result: %r, errors: %s' % (answer.sent_cmd.cmd, 
                                                 answer.result, answer.error)

    def _get_answer(self, answers, cmd):
        cmd = self._get_cmd_str(cmd)
        for ans in answers:
            if ans.sent_cmd.cmd == cmd:
                return ans
    
    def get_conn(self):
        return self._subprocess_conn
    
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
                       ' Exitcode: %r' % self._subprocess.exitcode)
            end()
            return answer
        
        self.send(self._kill_command)

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


def smoke_test_module():
    class TR(object):
        def test(self):
            pass
    base = ChildBase()
    base.log.d(base.cmd(TR.test))
    base.log.d('Debug')
    base.log.i('Info')
    test_path = 'smoothtest.tests.example.Example.Example.test_example'
    base.log.i(base.split_test_path(test_path))
    base.log.i(base.split_test_path(test_path, meth=True))
    class PBTest(ParentBase):
        def dummy_cmd(self, *args, **kwargs):
            self.log.d(str(args))
            self.log.d(str(kwargs))
            return 'dummy answer'
    pb = PBTest()
    def build_callback(secs):
        def callback(conn):
            import time
            pb.log('Child callback')
            time.sleep(secs)
            while True:
                pb._dispatch_cmds(conn)
        return callback
    pb.start_subprocess(build_callback(0), pre='Child1')
    args = (1, 'two', set()) 
    kwargs = dict(example=30)
    pb.send(pb.dummy_cmd, *args, **kwargs)
    ans = pb.recv()[0]
    pb.log.d(ans)
    assert ans.sent_cmd.args == args
    assert ans.sent_cmd.kwargs == kwargs
    pb.kill(block=True, timeout=0.1)
    pb.start_subprocess(build_callback(0.5), pre='Child2')
    pb.kill(block=True, timeout=0.1)


if __name__ == "__main__":
    smoke_test_module()

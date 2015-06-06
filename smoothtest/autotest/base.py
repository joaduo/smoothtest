# -*- coding: utf-8 -*-
'''
Smoothtest

Copyright (c) 2014, Juju inc.
Copyright (c) 2011-2013, Joaquin G. Duo

'''
import rel_imp
rel_imp.init()
from ..base import SmoothTestBase
from collections import namedtuple
import multiprocessing
from types import MethodType, FunctionType
import sys
import signal


AutotestCmd = namedtuple('AutotestCmd', 'cmd args kwargs')
AutotestAnswer = namedtuple('AutotestAnswer', 'sent_cmd result error')


class AutoTestBase(SmoothTestBase):
    pass


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
        # Make it ready for sending
        return [self._cmd(self._get_cmd_str(cmd), *args, **kwargs)]

    def _cmd(self, cmd, *args, **kwargs):
        # use when queying several commands
        return AutotestCmd(cmd, args, kwargs)


class TargetFunction(SmoothTestBase):

    def __init__(self, callback, parent_conn, child_conn, pre, close_stdin,
                 disable_key_int):
        self.callback = callback
        self.parent_conn = parent_conn
        self.child_conn = child_conn
        self.pre = pre
        self.close_stdin = close_stdin
        self.disable_key_int = disable_key_int

    def _disable_keyboard_interrupt(self):
        def signal_handler(signal, frame):
            self.log.i('Ignoring keyboard interrupt')
        signal.signal(signal.SIGINT, signal_handler)

    def __call__(self, *args, **kwargs):
        self.parent_conn.close()
        self.log.set_pre_post(pre=self.pre)
        if self.close_stdin:
            self.log.d('Closing stdin')
            sys.stdin.close()
        if self.disable_key_int:
            self._disable_keyboard_interrupt()
        self.log.d('Forked process callback starting...')
        self.callback(self.child_conn, *args, **kwargs)


class ParentBase(ChildBase):

    def start_subprocess(self, callback, args=(), kwargs={}, pre='',
                         close_stdin=True, disable_key_int=True):
        '''
        Start a subprocess child.

        :param callback: callback to start the subprocess
        :param pre: logging prefix
        :param close_stdin: close stdin in child after forking
        :param disable_key_int: disable keyboard interrupt on subprocess
        '''
        parent, child = multiprocessing.Pipe()
        # Add space if defined
        pre = pre if not pre else pre + ' '
        # Windows needs target to be pickable
        target = TargetFunction(callback, parent, child, pre, close_stdin,
                                disable_key_int)
        self._subprocess = multiprocessing.Process(target=target, args=args,
                                                   kwargs=kwargs)
        self._subprocess.start()
        self._subprocess_conn = parent
        child.close()

    def get_subprocess_pid(self):
        return self._subprocess.pid

    def restart_subprocess(self, callback, pre='', close_stdin=True):
        '''
        Kill subprocess (forcing) and restart it again.

        :param callback: callback in the subprocess
        '''
        self.kill(block=True, timeout=self._timeout)
        self.start_subprocess(callback, pre, close_stdin)

    def kill(self, block=False, timeout=None):
        '''
        Send the kill message to the subprocess.
        To force do block=True, timeout=0.1, for example.

        :param block: block until the subprocess is killed
        :param timeout: seconds to wait before timing out and forcing the kill
            (only works in blocking mode)
        '''
        return self._kill_subprocess(block, timeout)

    def send(self, cmd, *args, **kwargs):
        '''
        Non-blocking scheduling of a remote command.

        :param cmd: command string or method instance
        :param args: *args of the remote command
        :param kwargs: **kwargs of the remote command
        '''
        self._subprocess_conn.send(self.cmd(cmd, *args, **kwargs))

    def recv(self):
        '''
        Receive a list of answer for previous commands sent. (blocking)
        '''
        return self._subprocess_conn.recv()

    def send_recv(self, cmd, *args, **kwargs):
        '''
        Send 1 command and receive the answer for that command (blocking)

        :param cmd: command string or method instance
        :param args: *args of the remote command
        :param kwargs: **kwargs of the remote command
        '''
        self.send(cmd, *args, **kwargs)
        return self._get_answer(self.recv(), cmd)

    def call_remote(self, cmd, *args, **kwargs):
        '''
        Calling a remote method is a transparent way of accessing a remote
        method. (blocking)
        It's the same as send_recv but you get the return value unpacked
        automatically.

        :param cmd: command string or method instance
        :param args: *args of the remote command
        :param kwargs: **kwargs of the remote command
        '''
        return self.send_recv(cmd, *args, **kwargs).result

    def poll(self):
        return self._subprocess_conn.poll()

    def fmt_answers(self, msg):
        output = ''
        for ans in msg:
            output += str(self._fmt_answer(ans)) + '\n'
        return output

    def _fmt_answer(self, answer):
        return 'cmd:%s result:%r error:%r' % (answer.sent_cmd.cmd,
                                              answer.result, answer.error)

    def _get_answer(self, answers, cmd):
        cmd = self._get_cmd_str(cmd)
        # Get the latest cmd matching
        for ans in reversed(answers):
            if ans and ans.sent_cmd.cmd == cmd:
                return ans

    def get_conn(self):
        return self._subprocess_conn

    def _kill_subprocess(self, block=False, timeout=None):
        self.log.d('Killing subprocess with pid %r.' % self._subprocess.ident)
        answer = None

        def end():
            if self._subprocess:
                self._subprocess.join()
                self._suprocess = None
            if self._subprocess_conn:
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
            answer = self._get_answer(self.recv(), self._kill_command)
            assert answer, 'No answer for the kill command sent.'
            self.log.d('Received kill answer %s' % self._fmt_answer(answer))
            pid, status = self._subprocess.ident, self._subprocess.exitcode
            self.log.i('Child with pid {pid} gently terminated with exit '
                       'status {status}.'.format(pid=pid, status=status))
        else:
            self._subprocess.terminate()
            pid, status = self._subprocess.ident, self._subprocess.exitcode
            self.log.w('Child pid {pid} killed by force with exit status '
                       '{status}.'.format(pid=pid, status=status))
        end()
        return answer


def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()

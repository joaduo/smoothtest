# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import time
import unittest
from smoothtest.autotest.base import ChildBase, ParentBase


class ParebBaseTest(ParentBase):
    _dummy_answer = 'dummy answer'

    def dummy_cmd(self, *args, **kwargs):
        self.log.d(str(args))
        self.log.d(str(kwargs))
        return self._dummy_answer


def pickable_callback(conn, pb, secs):
    pb.log('Child callback')
    time.sleep(secs)
    while True:
        pb._dispatch_cmds(conn)


class Test(unittest.TestCase):

    def test_parent_base(self):
        pb = ParebBaseTest()
        # Start pickable callback (listening events)
        pb.start_subprocess(pickable_callback, args=(pb, 0), pre='Child1')
        # No make a remote call
        args = (1, 'two', set())
        kwargs = dict(example=30)
        ans = pb.send_recv(pb.dummy_cmd, *args, **kwargs)
        pb.log.d(ans)
        # Check we get the same args and kwargs
        assert ans.sent_cmd.args == args
        assert ans.sent_cmd.kwargs == kwargs
        # Kill first subprocess
        pb.kill(block=True, timeout=0.1)
        # Start a new one, and kill it forcing
        pb.start_subprocess(pickable_callback, args=(pb, 0.5), pre='Child2')
        pb.kill(block=True, timeout=0.1)

    def test_child_base(self):
        class TR(object):

            def test(self):
                pass
        base = ChildBase()
        base.log.d(base.cmd(TR.test))
        base.log.d('Debug')
        base.log.i('Info')
        test_path = 'smoothtest.tests.example.test_Example.Example.test_example'
        base.log.i(base.split_test_path(test_path))
        base.log.i(base.split_test_path(test_path, meth=True))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

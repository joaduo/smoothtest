# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
from .AutotestContext import singleton_decorator
import multiprocessing
import sys
from cStringIO import StringIO

@singleton_decorator
class AutotestNotebook(object):
    def init_notebook(self):
        parent_pipe, child_pipe = multiprocessing.Pipe()
        self.parent_pipe = parent_pipe
        pid = os.fork()
        if pid: #parent
            #Child will use this pipe
            child_pipe.close()
            #Start Ipython!
            from IPython import embed
            embed()
            raise SystemExit(0)
        else: #child
            #Setup IO
            #keep old stdout and stderr
            self._stdout,  self._stderr = sys.stdout, sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            #Close input, parent will listen to it
            sys.stdin.close()
            #This pipe is not needed (parent will use it)
            parent_pipe.close()
            return child_pipe

def smoke_test_module():
    pass

if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
import pickle

class PipeIpc(object):
    def __init__(self, in_pipe, out_pipe):
        self._in_file = self._get_file('in', in_pipe)
        self._out_file = self._get_file('out', out_pipe)
    
    def _get_file(self, direction, pipe):
        r,w = pipe
        r,w = os.fdopen(r,'r',0), os.fdopen(w,'w',0)
        if direction == 'out':
            r.close()
            return w
        elif direction == 'in':
            w.close()
            return r
    
    def write(self, msg):
        return self._out_file.write(self._serialize(msg))
    
    def read(self):
        return self._deserialize(self._in_file.read())

    def _serialize(self, msg):
        return pickle.dumps(msg, protocol=pickle.HIGHEST_PROTOCOL)

    def _deserialize(self, msg):
        return pickle.loads(msg)
    
    def close(self):
        self._in_file.close()
        self._out_file.close()



def smoke_test_module():
    in_pipe = os.pipe() 
    out_pipe = os.pipe()
    pid = os.fork()
    if pid: #parent
        pi = PipeIpc(in_pipe, out_pipe)
        import time
        time.sleep(1)
        pi.write('hello child')
#        print pi.read()
        pi.close()
    else:
        pi = PipeIpc(out_pipe, in_pipe)
        print pi.read()
#        pi.write('hello parent')
        pi.close()

if __name__ == "__main__":
    smoke_test_module()

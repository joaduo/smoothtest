# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from .base import AutoTestBase
from multiprocessing import Process, Pipe

class TestSearcher(AutoTestBase):
    def _build_solve_paths(self, test_path_regex, *test_path_regexes):
        def solve_paths(conn):
    
    def solve_paths(self, test_path_regex, *test_path_regexes):
        #We need to create a new process to avoid importing the modules
        #in the parent process
        
        def f(conn):
            conn.send([42, None, 'hello'])
            conn.close()
            
        parent_conn, child_conn = Pipe()
        p = Process(target=f, args=(child_conn,))
        p.start()
        print parent_conn.recv()   # prints "[42, None, 'hello']"
        p.join()


        
        if __name__ == '__main__':



def smoke_test_module():
    pass    

if __name__ == "__main__":
    smoke_test_module()

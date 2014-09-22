# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

from IPython.core.magic import Magics, magics_class, line_magic

import shlex
import subprocess
from pprint import pformat


@magics_class
class AutotestMagics(Magics):
    main = None
    
    def expand_files(self, tests):
        p = subprocess.Popen(['bash'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = p.communicate('echo %s'%(' '.join(tests)))
        if err:
            raise LookupError('Couldn\'t expand with bash files {tests}\n'
                              ' Error:{err}'.format(tests=tests, err=err))
        return shlex.split(out)
    
    @line_magic
    def t(self, line):
        "my line magic"
        from .Command import Command
        from .TestSearcher import TestSearcher
        command = Command()
        parser = command.get_parser(file_checking=False)
        args = parser.parse_args(shlex.split(line))
        expanded = self.expand_files(args.tests)
        args.tests = expanded
        test_config = command.parcial(args)
#        ts = TestSearcher()
#        ts_args = [] 
#        for path in expanded:
#            tst = command._clean_path(path)
#            ts_args.append((tst, args.methods_regex))
#        test_paths, parcial_reloads = ts.solve_paths(*ts_args)
#        test_config = dict(test_paths=test_paths, parcial_reloads=parcial_reloads, 
#                           full_reloads=[], smoke=args.smoke)
        self.main.send_tests(**test_config)
        return list(test_config['test_paths'])
    
    @line_magic
    def test(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return line

def load_extension(ipython, main):
    AutotestMagics.main = main
    ipython.register_magics(AutotestMagics)

def load_ipython_extension(ipython):
    ip = ipython
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(AutotestMagics)



def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass

def smoke_test_module():
    AutotestMagics()
    

if __name__ == "__main__":
    smoke_test_module()

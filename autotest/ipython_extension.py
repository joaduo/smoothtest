# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

from IPython.core.magic import Magics, magics_class, line_magic
from smoothtest.autotest.Main import Main

@magics_class
class MyMagics(Magics):

    @line_magic
    def t(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        print('an = %s'%(dir(Main())))
        return line
    
    @line_magic
    def test(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return line

def load_ipython_extension(ipython):
    # The `ipython` argument is the currently active `InteractiveShell`
    # instance, which can be used in any way. This allows you to register
    # new magics or aliases, for example.

    # In order to actually use these magics, you must register them with a
    # running IPython.  This code must be placed in a file that is loaded once
    # IPython is up and running:
    ip = ipython
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(MyMagics)



def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass



def smoke_test_module():
    pass    

if __name__ == "__main__":
    smoke_test_module()

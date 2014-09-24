# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

from IPython.core.magic import Magics, magics_class, line_magic

import shlex
import subprocess


@magics_class
class AutotestMagics(Magics):
    main = None

    def expand_files(self, tests):
        #TODO: use glob
        p = subprocess.Popen(['bash'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = p.communicate('echo %s' % (' '.join(tests)))
        if err:
            raise LookupError('Couldn\'t expand with bash files {tests}\n'
                              ' Error:{err}'.format(tests=tests, err=err))
        return shlex.split(out)

    @line_magic
    def autotest(self, line):
        '''
        
        :param line:
        '''
        from .Command import Command
        command = Command()
        parser = command.get_extension_parser()
        args = parser.parse_args(shlex.split(line))
        args.tests = self.expand_files(args.tests)
        args.full_reloads = self.expand_files(args.full_reloads)
        test_config = command.parcial(args)
        test_config.update(force=args.force)
        self.main.send_test(**test_config)
        return test_config


def load_extension(ipython, main):
    AutotestMagics.main = main
    ipython.register_magics(AutotestMagics)


def load_ipython_extension(ipython):
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ipython.register_magics(AutotestMagics)


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass


def smoke_test_module():
    AutotestMagics()


if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from IPython.core.magic import Magics, magics_class, line_magic
import shlex
import glob
from argparse import ArgumentParser


@magics_class
class AutotestMagics(Magics):
    main = None

    def expand_files(self, tests):
        paths = []
        for tst in tests:
            paths += glob.glob(tst)
        return paths

    def __common(self, line):
        from .Command import Command
        command = Command()
        parser = command.get_extension_parser()
        args, unknown = parser.parse_known_args(shlex.split(line))
        args.tests = self.expand_files(args.tests)
        args.full_reloads = self.expand_files(args.full_reloads)
        test_config = command.get_test_config(args, unknown)
        test_config.update(force=args.force)
        return args, test_config
    
    def _send(self, test_config):
        self.main.send_test(**test_config)

    def _test_magic_cmd_parser(self):
        parser = ArgumentParser(description='Manually trigger a test.')
        parser.add_argument('-f', '--force', help='Trigger full reload.', 
                            default=False, action='store_true')
        return parser

    @line_magic
    def test(self, line):
        parser = self._test_magic_cmd_parser()
        args = parser.parse_args(shlex.split(line))
        if args.force:
            #Force full reload
            test_config = self.main.test_config.copy()
            test_config.update(force=True)
            self._send(test_config)
        else:
            #Simply invoque .test TODO
            self.main.test

    @line_magic
    def autotest(self, line):
        args, test_config = self.__common(line)
        if args.update:
            #Update set values
            for k,v in self.main.test_config.iteritems():
                if not test_config.get(k):
                    test_config[k] = v
            if args.smoke is not None:
                test_config['smoke'] = True
            if args.nosmoke is not None:
                test_config['smoke'] = False
            test_config.update(force=args.force)
        self._send(test_config)
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
    am = AutotestMagics(None)
    from pprint import pprint
    pprint( am.expand_files(['./*.py']))


if __name__ == "__main__":
    smoke_test_module()

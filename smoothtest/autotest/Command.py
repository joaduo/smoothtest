# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import os
import sys
import rel_imp
from xpathwebdriver.base import module_regex
import glob
rel_imp.init()
from argparse import ArgumentParser
from .base import AutoTestBase
from .Main import Main
from .TestSearcher import TestSearcher
from smoothtest.base import CommandBase, is_valid_file, is_file_or_dir
from smoothtest.settings.solve_settings import solve_settings


class Command(AutoTestBase, CommandBase):

    def get_epilog(self, cmd_name='autotest'):
        return '''
== Autotest Guide

For an detailed introduction in the usage of the autotest command, plase visit:
https://github.com/joaduo/smoothtest/blob/master/smoothtest/autotest/AutotestGuide.md

Or the bundled file smoothtest/autotest/AutotestGuide.md with this installation

== Smoothtest configuration

For the options that smoothtest accepts you can consult the file at:
https://github.com/joaduo/smoothtest/blob/master/smoothtest/settings/default.py

Or file smoothtest/settings/default.py bundled in this installation

== Example commmands

{cmd_name} # starts autotest CLI

{cmd_name} <path to test_file.py> # autotest CLI with that test selected
{cmd_name} <python.like.module.path.to.test> # same as above but using dot paths


        '''.format(**locals())

    def get_parser(self):
        parser = ArgumentParser(description='Automatically runs (unit) '
                                'tests upon code/file changes.')
        parser.add_argument(
            'tests',
            type=is_valid_file,
            help='Tests\' files or modules path to  to be monitored.'
            ' Changes on these files trigger a reload of those same modules '
            'and rerunning the tests they contain.',
            default=tuple(),
            nargs='*')
        parser.add_argument(
            '-r',
            '--methods-regex',
            type=str,
            help='Specify regex for Methods matching',
            default='')
        parser.add_argument(
            '-n',
            '--no-ipython',
            help='Do not embed ipython'
            ' interactive shell as UI.',
            default=False,
            action='store_true')
        parser.add_argument(
            '-B',
            '--no-browser',
            help='Do not start webdriver\'s browser',
            default=False,
            action='store_true')
        parser.add_argument(
            '--smoke',
            help='Do not run tests. Simply test'
            ' the whole monitoring system',
            default=None,
            action='store_true')
        parser.add_argument(
            '-F',
            '--full-reloads',
            type=is_file_or_dir,
            help='Files or directories to be monitored. They will trigger '
            'reloading all files involved and rerunning tests.',
            default=tuple(),
            nargs='+')
        parser.add_argument(
            '-m',
            '--fnmatch',
            type=str,
            help='Fnmatch '
            'pattern to filter files in full reloads directories.'
            ' (default=*.py)',
            default='*.py')
        self._add_smoothtest_common_args(parser)
        return parser

    def get_extension_parser(self):
        parser = self.get_parser()
        parser.add_argument(
            '-f',
            '--force',
            help='force reloading tests '
            '(also restarting webdriver)',
            default=False,
            action='store_true')
        parser.add_argument('-u', '--update', help='update test config',
                            default=False, action='store_true')
        parser.add_argument('--nosmoke', help='force non-smoke mode for'
                            ' updating', default=None, action='store_true')
        return parser

    def expand_paths(self, paths):
        new_paths = []
        for tst in paths:
            if module_regex.match(tst):
                new_paths.append(tst)
            else:
                new_paths += glob.glob(tst)
        return new_paths

    def get_test_config(self, args, argv):
        searcher = TestSearcher()
        test_paths = set()
        partial_reloads = set()
        for path in self.expand_paths(args.tests):
            path = self._path_to_modstr(path)
            paths, partial = searcher.solve_paths((path, args.methods_regex))
            if paths:
                test_paths.update(paths)
                partial_reloads.update(partial)

        test_config = dict(test_paths=test_paths,
                           partial_reloads=partial_reloads,
                           full_reloads=self.expand_paths(args.full_reloads),
                           full_filter=args.fnmatch,
                           smoke=args.smoke,
                           argv=argv,
                           )
        return test_config

    def main(self, argv=None):
        curdir = os.path.abspath(os.curdir)
        filedir = os.path.abspath(os.path.dirname(__file__))

        # Remove the dir of this file if we are not in this directory
        if curdir != filedir and filedir in sys.path:
            sys.path.remove(filedir)

        args, unkonwn = self.get_parser().parse_known_args(argv)
        self._process_common_args(args)

        # Run autotest Main loop (ipython UI + subprocesses)
        main = Main()
        if args.no_browser:
            solve_settings().set('webdriver_enabled', False)
        test_config = self.get_test_config(args, unkonwn)
        main.run(embed_ipython=not args.no_ipython, test_config=test_config)


def smoke_test_module():
    c = Command()
    c.get_parser()
    parser = c.get_extension_parser()
    args, unkown = parser.parse_known_args([])
    c.get_test_config(args, unkown)
    mod_path = 'fulcrum.views.tests.home'
    is_valid_file(mod_path)
    is_file_or_dir(mod_path)
    mod_file = 'fulcrum/views/tests/home.py'
    is_valid_file(mod_file)
    is_file_or_dir(mod_file)


def main(argv=None):
    Command().main(argv)

if __name__ == "__main__":
    main()

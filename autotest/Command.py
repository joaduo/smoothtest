# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
import os
import re
from argparse import ArgumentParser
from smoothtest.autotest.base import AutoTestBase
from smoothtest.autotest.Main import Main
from smoothtest.autotest.TestSearcher import TestSearcher

def is_valid_file(parser, path):
    '''
    Validate if a passed argument is a existing file (used by argsparse)
    '''
    abspath = os.path.abspath(path)
    if os.path.exists(abspath) and os.path.isfile(abspath):
        return path  # return the file path
    else:
        parser.error("The file %s does not exist!" % path)
        
def is_file_or_dir(parser, path):
    '''
    Validate if a passed argument is a existing file (used by argsparse)
    '''
    abspath = os.path.abspath(path)
    if os.path.exists(abspath) and (os.path.isfile(abspath) or os.path.isdir(abspath)):
        return path  # return the file path
    else:
        parser.error("The file %s does not exist!" % path)

class Command(AutoTestBase):
    def __init__(self):
        pass
    
    def get_parser(self, file_checking=True):
        if file_checking:
            is_file = lambda x: is_valid_file(parser, x)
            is_dir_file = lambda x: is_file_or_dir(parser, x)
        else:
            is_file = lambda x:x
            is_dir_file = lambda x:x
        parser = ArgumentParser(description='Start a local sales vs non-sales glidepath server')
        parser.add_argument('tests', type=is_file,
                            help='Tests to be monitored and run. Triggers parcial_reloads',
                            default=[], nargs='*')
        parser.add_argument('-r', '--methods-regex', type=str,
                            help='Specify regex for Methods matching',
                            default='')
        parser.add_argument('-n', '--no-ipython',
                            help='Do not use ipython interactive shell',
                            default=False, action='store_true')
        parser.add_argument('--smoke',
                            help='Do not run tests. Simply test the whole monitoring system',
                            default=False, action='store_true')
        parser.add_argument('-f', '--full-reloads', type=is_dir_file,
                            help='Files or directories to be monitored and triggers of full_reloads.',
                            default=None, nargs='?')
#        parser.add_argument('-n', '--no-debug', default=False, action='store_true')
#        parser.add_argument('-p', '--paste', default=False, action='store_true')
#        parser.add_argument('-s', '--sales', default=False, action='store_true')
        return parser
        
    def claen_path(self, tst):
        tst = tst.replace(os.path.sep, '.')
        tst = re.sub(r'\.(pyc)|(py)$', '', tst).strip('.')
        return tst
    
    def main(self, argv=None):
        args = self.get_parser().parse_args(argv)
        searcher = TestSearcher()
        test_paths = set()
        parcial_reloads = set()
        for tst in args.tests:
            tst  = self.claen_path(tst)
            paths, parcial = searcher.solve_paths((tst, args.methods_regex))
            if paths:
                test_paths.update(paths)
                parcial_reloads.update(parcial)
        main = Main(smoke=args.smoke)
        test_config = dict(test_paths=test_paths, parcial_reloads=parcial_reloads)
        child_callback = main.build_callback(**test_config)
        main.run(child_callback, embed_ipython=not args.no_ipython)

def main(argv=None):
    Command().main(argv)

if __name__ == "__main__":
    main()

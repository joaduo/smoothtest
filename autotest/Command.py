# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import relative_import
from .base import AutoTestBase
from argparse import ArgumentParser
import os

def is_valid_file(parser, arg):
    '''
    Validate if a passed argument is a existing file (used by argsparse)
    '''
    arg = os.path.abspath(arg)
    if os.path.exists(arg) and os.path.isfile(arg):
        return arg  # return the file path
    else:
        parser.error("The file %s does not exist!" % arg)
        
def is_file_or_dir(parser, arg):
    '''
    Validate if a passed argument is a existing file (used by argsparse)
    '''
    arg = os.path.abspath(arg)
    if os.path.exists(arg) and (os.path.isfile(arg) or os.path.isdir(arg)):
        return arg  # return the file path
    else:
        parser.error("The file %s does not exist!" % arg)

class Command(AutoTestBase):
    def __init__(self):
        pass
    
    def get_parser(self):
        parser = ArgumentParser(description='Start a local sales vs non-sales glidepath server')
        parser.add_argument('tests', type=lambda x: is_valid_file(parser, x),
                            help='Tests to be monitored and run. Triggers parcial_reloads',
                            default=None, nargs='+')
        parser.add_argument('-r', '--regex',
                            help='Tests to be monitored and run. Triggers parcial_reloads',
                            default=False, action='store_true')
        parser.add_argument('-m', '--methods', type=str,
                            help='Tests to be monitored and run. Triggers parcial_reloads',
                            default=None, nargs=1)
        parser.add_argument('-f', '--full-reloads', type=lambda x: is_file_or_dir(parser, x),
                            help='Files or directories to be monitored and triggers of full_reloads.',
                            default=None, nargs='?')
#        parser.add_argument('-n', '--no-debug', default=False, action='store_true')
#        parser.add_argument('-p', '--paste', default=False, action='store_true')
#        parser.add_argument('-s', '--sales', default=False, action='store_true')
        return parser
        
    def main(self, argv=None):
        args = self.get_parser().parse_args(argv)
        print args

def main(argv=None):
    Command().main(argv)

if __name__ == "__main__":
    main()

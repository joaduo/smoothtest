# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''


def smoke_test_module():
    ''' Simple self-contained test for the module '''
    import logging
    logging.info('Example smoke test')

if __name__ == '__main__':
    smoke_test_module()

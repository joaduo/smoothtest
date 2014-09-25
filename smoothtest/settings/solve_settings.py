# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

def solve_settings():
    try:
        from smoothtest_settings import Settings
    except ImportError:
        from smoothtest.settings.default import DefaultSettings as Settings
    return Settings()


def smoke_test_module():
    print solve_settings()

if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import xpathwebdriver.solve_settings as xsolve_settings


def register_settings(settings_path):
    xsolve_settings.register_settings(settings_path)
    set_log_level()


def solve_settings():
    return xsolve_settings._solve_settings('smoothtest.settings.default')


def set_log_level():
    # Set the level of the root logger
    # import here due chicke-egg problem
    from smoothtest.base import SmoothTestBase
    from smoothtest.Logger import Logger
    xsolve_settings._set_log_level(SmoothTestBase, Logger)
    xsolve_settings.set_log_level()


def smoke_test_module():
    global called_once
    called_once = True
    solve_settings()


if __name__ == "__main__":
    smoke_test_module()

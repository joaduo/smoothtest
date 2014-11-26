# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

class SettingsWrapper(object):
    def __init__(self, settings):
        self._settings = settings

    def get(self, name, default=None):
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        return default


def solve_settings():
    try:
        from smoothtest_settings import Settings
    except ImportError:
        from smoothtest.settings.default import DefaultSettings as Settings
    return SettingsWrapper(Settings())


def smoke_test_module():
    print solve_settings()

if __name__ == "__main__":
    smoke_test_module()

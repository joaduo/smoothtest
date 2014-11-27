# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import imp


#TODO: support .cfg files
class SettingsWrapper(object):
    '''
    Provide the .get(name, default=None) method for accessing an object's 
    attributes.
    Useful for configuration.
    '''
    def __init__(self, settings):
        self._settings = settings

    def get(self, name, default=None):
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        return default


global_settings = None
def register_settings(settings_path):
    '''
    Register settings given specific module path.
    :param settings_path:
    '''
    #TODO:Py3
    #http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    mod = imp.load_source('specific_smoothtest_settings', settings_path)
    global global_settings
    global_settings = SettingsWrapper(mod.Settings())


def solve_settings():
    '''
    Main function for getting smoothtest global settings.
    #TODO: this goes against any Encapsulated Environment Pattern (context)
    '''
    if global_settings:
        return global_settings
    else:
        try:
            from smoothtest_settings import Settings
        except ImportError:
            from smoothtest.settings.default import DefaultSettings as Settings
        return SettingsWrapper(Settings())


def smoke_test_module():
    print solve_settings()

if __name__ == "__main__":
    smoke_test_module()

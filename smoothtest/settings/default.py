# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

class DefaultSettings(object):
    production = False

    web_server_url = ''
    
    webdriver_browser = 'PhantomJS'
    webdriver_pooling = False
    webdriver_pool_size = 1
    webdriver_inmortal_pooling = False
    webdriver_keep_open = False

    screenshots_enabled = False
    screenshots_level = 0


def smoke_test_module():
    DefaultSettings()

if __name__ == "__main__":
    smoke_test_module()
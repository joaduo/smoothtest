# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''

class DefaultSettings(object):
    production = False

    web_server_url = ''
    
    virtual_display_enable = False
    virtual_display_visible = False
    virtual_display_size = (800,600)
    virtual_display_keep_open = False

    webdriver_browser = 'PhantomJS'
    webdriver_pooling = False
    webdriver_pool_size = 1
    webdriver_inmortal_pooling = False
    webdriver_keep_open = False

    screenshot_level = 0


def smoke_test_module():
    DefaultSettings()

if __name__ == "__main__":
    smoke_test_module()

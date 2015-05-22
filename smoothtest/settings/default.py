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
    virtual_display_size = (800, 600)
    virtual_display_keep_open = False

    webdriver_browser = 'PhantomJS'
    webdriver_pooling = False
    webdriver_pool_size = 1
    webdriver_inmortal_pooling = False
    webdriver_keep_open = False

    # Browsers profiles
    # Eg: '/home/<user>/.mozilla/firefox/4iyhtofy.webdriver_autotest' on linux
    # or: 'C:/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/c1r3g2wi.default' on windows
    webdriver_firefox_profile = None

    screenshot_level = 0
    screenshot_exceptions_dir = './'


def smoke_test_module():
    DefaultSettings()

if __name__ == "__main__":
    smoke_test_module()

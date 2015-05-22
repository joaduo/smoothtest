# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''


class DefaultSettings(object):
    # Signal that we are working on production. To disable write tests
    production = False

    # Server to be tested URL eg: http://www.example.com 
    web_server_url = ''

    # Virtual display is useful to keep the webdriver browser contained
    # avoiding the browser to pop-up abover other windows (with alerts for example)
    virtual_display_enable = False # Use virtual display
    virtual_display_visible = False # Show the virtual display or may be hidden (for headless testing)
    virtual_display_size = (800, 600) # Dimensions of the virtual display
    virtual_display_keep_open = False   # Keep the virtual display after a smoothtest 
                                    # process finished (useful when we also keep the browser open for debugging) 

    webdriver_browser = 'PhantomJS' # Which browser we would like to use webdriver with: Firefox, Chrome, PhantomJs, etc...
    webdriver_pooling = False # Reuse webdrivers across tests (WIP)
    webdriver_pool_size = 1
    webdriver_inmortal_pooling = False # Reuse webdrivers across tests rounds (WIP)
    webdriver_keep_open = False # Keep the browser open after a smoothtest process finished (for debugging/testing)

    # Browsers profiles
    # Eg: '/home/<user>/.mozilla/firefox/4iyhtofy.webdriver_autotest' on linux
    # or: 'C:/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/c1r3g2wi.default' on windows
    webdriver_firefox_profile = None

    screenshot_level = 0 # Like a text logging level, but doing screenshots (WIP) 
                        # Higher level-> more screenshots per action
    screenshot_exceptions_dir = './' # Were to save logged screenshot


def smoke_test_module():
    DefaultSettings()

if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import logging

# Webdriver life level
#GOD_LIFE = 7 # Browser survives across universes (WIP)
#AI_LIFE = 6 # Browser survives across reboots and becomes agent smith (WIP)
INMORTAL_LIFE = 5 # Browser survives across processes
PROCESS_LIFE = 4 # Browser is alive as long as the smoothtest process is running
TEST_RUNNER_LIFE = 3 # Browser is alive as long as the TestRunner process is running (new test runner process means new browser) 
TEST_ROUND_LIFE = 2 # Browser is alive for a single test round
SINGLE_TEST_LIFE = 1 # Start 1 new browser per test ran

class DefaultSettings(object):
    # Signal that we are working on production. To disable write tests
    production = False

    @property
    def base_url(self):
        return self.web_server_url

    # Server to be tested URL eg: http://www.example.com 
    web_server_url = ''

    # Virtual display is useful to keep the webdriver browser contained
    # avoiding the browser to pop-up abover other windows (with alerts for example)
    virtual_display_enable = False # Use virtual display
    virtual_display_visible = False # Show the virtual display or may be hidden (for headless testing)
    virtual_display_backend = None # 'xvfb', 'xvnc' or 'xephyr', ignores ``virtual_display_visible``
    virtual_display_size = (800, 600) # Dimensions of the virtual display
    virtual_display_keep_open = False   # Keep the virtual display after a smoothtest 
                                    # process finished (useful when we also keep the browser open for debugging) 

    webdriver_browser = 'PhantomJS' # Which browser we would like to use webdriver with: Firefox, Chrome, PhantomJs, etc...
    webdriver_browser_life = TEST_ROUND_LIFE # Level of life of the webdriver browser
    webdriver_pool_size = 1
    webdriver_keep_open = False # Keep latest browser open after a smoothtest process finished (for debugging/testing)

    # Browsers profiles
    # Eg: '/home/<user>/.mozilla/firefox/4iyhtofy.webdriver_autotest' on linux
    # or: 'C:/Users/<user>/AppData/Roaming/Mozilla/Firefox/Profiles/c1r3g2wi.default' on windows
    webdriver_firefox_profile = None

    screenshot_level = 0 # Like a text logging level, but doing screenshots (WIP) 
                        # Higher level-> more screenshots per action
    screenshot_exceptions_dir = './' # Were to save logged screenshot
    
    assert_screenshots_dir = '/tmp/'
    assert_screenshots_learning = False
    assert_screenshots_failed_dir = '/tmp/'

    log_level_default = logging.INFO
    log_level_root_handler = logging.DEBUG


def smoke_test_module():
    DefaultSettings()

if __name__ == "__main__":
    smoke_test_module()

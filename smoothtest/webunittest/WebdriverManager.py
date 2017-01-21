'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from xpathwebdriver.webdriver_manager import WebdriverManager

def smoke_test_module():
    from smoothtest.settings.default import TEST_ROUND_LIFE
    mngr = WebdriverManager()
    lvl = mngr.enter_level(level=TEST_ROUND_LIFE)
    ffox = lvl.acquire_driver()
    mngr.list_webdrivers()
    lvl.exit_level()
    mngr.stop_display()
    mngr.quit_all_webdrivers()


if __name__ == "__main__":
    smoke_test_module()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from xpathwebdriver.xpath_browser import XpathBrowser

XpathBrowser = XpathBrowser


def smoke_test_module():
    from smoothtest.webunittest.WebdriverManager import WebdriverManager
    mngr = WebdriverManager()
#    mngr.setup_display()
#    webdriver = mngr.new_webdriver()
    u = u'https://www.google.cl/?gfe_rd=cr&ei=ix0kVfH8M9PgwASPoIFo&gws_rd=ssl'
    print XpathBrowser.Url(u).get_path_and_on()
#    browser = XpathBrowser('', webdriver)
#    browser.get_page('http://www.google.com')
#    browser.log.i(browser.current_path())


if __name__ == "__main__":
    smoke_test_module()


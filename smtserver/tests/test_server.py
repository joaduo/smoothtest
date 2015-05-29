# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
import rel_imp; rel_imp.init()
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.settings.default import TEST_ROUND_LIFE
from ..SmoothtestServer import port
import requests
import simplejson

base_url = 'http://localhost:%s' % port

class TestXpathBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to enter "single test level" of life for each test
        # It will initialize the webdriver if no webdriver is present from upper levels
        cls._level_mngr = WebdriverManager().enter_level(level=TEST_ROUND_LIFE)
        # Get Xpath browser
        cls.browser = cls._level_mngr.get_xpathbrowser(name=__name__)
        cls.browser.set_base_url(base_url)
    
    @classmethod
    def tearDownClass(cls):
        cls._level_mngr.exit_level()

    def test_loaded(self):
        jsondata = {'this':123, "author":"wee","message":"test"}
        data = {'test_result':simplejson.dumps(jsondata),
                }
        r = requests.post(base_url + '/submit', data)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
from selenium.common.exceptions import UnexpectedAlertPresentException
from smoothtest.webunittest.tests.base import WebUnitTestBase


class TestXpathBrowser(WebUnitTestBase):
    '''
    TODO:
    - test fill
    - test select/has/extract 
    - get_url (with condition)
    - get_path (with condition)
    - test wait
    '''

    def test_dismiss_alert(self):
        body = '''
          <script type="text/javascript">
            alert('Example alert');
          </script>
        '''
        try:
            with self.create_html('test_dismiss_alert', body) as path:
                self.get_local_page(path)
        except UnexpectedAlertPresentException:
            self.browser.wipe_alerts()

    def test_click(self):
        body = "<button id='example_button'>Example</button>"
        with self.create_html('test_click', body) as path:
            self.get_local_page(path)
            self.browser.click('.//button')
            self.browser.click(".//*[@id='example_button']")
            
    def test_select(self):
        body = '''
          <div>
              <div id='some_text'>
                <p>The quick fox jumped over the Lorem Ipsum.</p>
              </div>
              <div id='some_other'>
                <p>The other quick fox jumped over the Lorem Ipsum.</p>
              </div>
          </div>
        '''
        with self.create_html('test_select', body) as path:
            self.get_local_page(path)
            self.browser.select_xpath('//div')
            self.browser.select_xsingle('//div')


if __name__ == "__main__":
    unittest.main()

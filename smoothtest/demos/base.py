# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import unittest
from smoothtest.webunittest.WebdriverManager import WebdriverManager
from smoothtest.Logger import Logger
from smoothtest.webunittest.XpathBrowser import XpathBrowser
import os
from contextlib import contextmanager
from smoothtest.settings.default import SINGLE_TEST_LIFE


class WebUnitTestBase(unittest.TestCase):

    def _get_local_html_path(self, name):
        return os.path.join(os.path.dirname(__file__), 'html', name)

    def _local_path_to_url(self, path):
        return 'file://' + path

    def get_local_page(self, path):
        self.browser.get_url(self._local_path_to_url(path))

    @contextmanager
    def create_html(self, name, body, jquery=True, **kwargs):
        templ = '''
<!DOCTYPE html>
<html>
<head>
  {jquery}
  <title>{name}</title>
</head>
<body>
      {body}
</body>
</html>
        '''
        if jquery:
            jquery = ''
        else:
            jquery = ''
        
        kwargs.update(locals())
        html = templ.format(**kwargs)
        path = self._get_local_html_path(name + '.html')
        with open(path, 'w') as fh:
            fh.write(html)
        try:
            yield  path
        except:
            raise
        finally:
            os.remove(path)

    def setUp(self):
        self.__level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        webdriver = self.__level_mngr.acquire_driver()
        logger = Logger(__name__)
        self.browser = XpathBrowser('', webdriver, logger, settings={})

    def tearDown(self):
        self.__level_mngr.leave_level()


def smoke_test_module():
    pass    

if __name__ == "__main__":
    smoke_test_module()

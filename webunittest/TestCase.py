'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import urlparse
from selenium import webdriver
import unittest
import time
from selenium.common.exceptions import WebDriverException

class WebdriverUtils(object):
    _implicit_wait = 30
    #Height, Width tuple
    _window_size = (800, 600)
    _shot_sizes = [(400,300), (800,600), (1024, 768)]
    __driver = None
    def __init__(self, base_url, browser='PhantomJS', webdriver=None):
        self._init_webdriver(base_url, browser, webdriver)
    
    def _init_webdriver(self, base_url, browser='PhantomJS', webdriver=None):
        if webdriver:
            self.__driver = webdriver
        else:
            self._init_driver(browser)
        self.get_driver().implicitly_wait(self._implicit_wait)
        self.get_driver().set_window_size(*self._window_size)            
        self._base_url = base_url
        
    def _quit_webdriver(self):
        self.__driver.quit()
        self.__driver = None

    def _init_driver(self, browser):
        if not self.__driver:
            #Firefox, Chrome, PhantomJS
            self.__driver = getattr(webdriver, browser)()
    
    def get_driver(self):
        assert self.__driver, 'driver was not initialized'
        return self.__driver

    def screenshot(self, *args, **kwargs):
        pass
    
    def get_page(self, path, base=None, check_load=False, condition=None):
        #default value
        base = base if base else self._base_url
        driver = self.get_driver()
        url = urlparse.urljoin(self._base_url, path)
        driver.get(url)
        if check_load:
            msg = 'Couldn\'t load page at %r.' % url
            assert self.wait_condition(condition), msg
        return driver
    
    def log_debug(self, msg):
        print msg
    
    _max_wait = 2
    _default_condition = 'return "complete" == document.readyState;'
    def wait_condition(self, condition=None):
        '''
        Active wait (polling) function, for a specific condition inside a page.
        '''
        condition = condition if condition else self._default_condition 
        if isinstance(condition, basestring):
            #Its a javascript script
            def condition_func(driver):
                return driver.execute_script(condition)
            condtn = condition_func
        else:
            condtn = condition
        #first start waiting a tenth of the max time
        parts = 10
        top = int(parts*self._max_wait)
        for i in range(1, top+1):
            loaded = condtn(self.get_driver())
            if loaded:
                self.log_debug('Condition "%s" is True.' % condition)
                break
            self.log_debug('Waiting condition "%s" to be True.' % condition)
            time.sleep(float(i)/parts)
        if not loaded:
            msg = ('Page took too long to load. Increase max_wait (secs) class'
                   ' attr. Or override _wait_script method.')
            self.log_debug(msg)
        return loaded    
    
    def _get_xpath_script(self, xpath, ret='node'):
        script = '''
var xpath = %(xpath)r;
var e = document.evaluate(xpath, document, null, 9, null).singleNodeValue;
        '''% locals()
        ret_dict = dict(
                        node='return e',
                        text='return e.textContent',
                        click='e.click()',
                        )
        script += '\n %s ;' % ret_dict.get(ret, ret)
        return script

    def select_xpath(self, xpath, ret='node'):
        dr = self.get_driver()
        try:
            e = dr.execute_script(self._get_xpath_script(xpath, ret))
        except WebDriverException as e:
            msg = 'WebDriverException: Could not select xpath {xpath!r}. Error: {e}'.format(**locals())
            raise LookupError(msg)
        if not e and ret == 'node':
            msg = 'Could not find a node at xpath %r' % xpath
            raise LookupError(msg)
        return e
    
    def extract_xpath(self, xpath, ret='text'):
        return self.select_xpath(xpath, ret)

    def fill_input(self, xpath, value):
        e = self.select_xpath(xpath)
        e.clear()
        e.send_keys(value)
        
    def click(self, xpath):
        e = self.select_xpath(xpath)
        e.click()

    def fill(self, xpath, value):
        self.fill_input(xpath, value)
        self.screenshot('fill', xpath, value)

class TestBase(WebdriverUtils):
    __global_webdriver = None
    @staticmethod
    def _new_webdriver(settings):
        #TODO: passing a webdriver factory, so we can cycle them
        #locking and releasing them
        if settings.webdriver_pooling:
            if not TestBase.__global_webdriver:
                browser = settings.webdriver_browser
                TestBase.__global_webdriver = getattr(webdriver, browser)()
            driver = TestBase.__global_webdriver
        else:
            driver = getattr(webdriver, browser)()
        return driver

    def _init_webserver_webdriver(self, settings=None, webdriver=None):
        from webunittest_settings import Settings
        self.settings = settings if settings != None else Settings()
        base_url = self.settings.web_server_url
        browser = self.settings.webdriver_browser
        webdriver = webdriver if webdriver else TestBase._new_webdriver(self.settings)
        self._init_webdriver(base_url, browser, webdriver)

    def _shutdown_webserver_webdriver(self):
        if (not self.settings.webdriver_keep_open and 
            not self.settings.webdriver_pooling):
            self._quit_webdriver()

##TODO decorator
#def branch(m):
#    return m

class TestCase(unittest.TestCase, TestBase):
    def assert_text(self, xpath, value):
        extracted = self.extract_xpath(xpath)
        msg = (u'Expecting {value} at {xpath}, but got {extracted}'.
               format(**locals()))
        self.assertEqual(extracted, value, msg)
        self.screenshot('assert_text', xpath, value) 

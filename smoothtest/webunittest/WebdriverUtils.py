# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import urlparse
import time
import logging
import re
import inspect
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from functools import wraps
from types import MethodType
from threading import Lock
from smoothtest.Logger import Logger
import urllib
import os


_with_screenshot = '_with_screenshot'
_zero_screenshot = '_zero_screenshot'


def zero_screenshot(method):
    '''
    Decorated method won't have any exception screenshot until we leave the method
    (means no screenshot on other methods called too)

    :param method: decorated method
    '''
    setattr(method, _zero_screenshot, True)
    return method


def screenshot(method):
    '''
    If the method raises an exception, take a screenshot.

    :param method: decorated method
    '''
    setattr(method, _with_screenshot, True)
    return method


def no_screenshot(method):
    '''
    No screenshot for exceptions at this decorated method.
    But any other method is free to take screenshots for any exception.

    :param method: decorated method
    '''
    setattr(method, _with_screenshot, False)
    return method


class WebdriverUtils(object):
    '''
    Utilities for making Webdriver more xpath-friendly.
    This class is designed to be framework independent, to be reused by other
    testing frameworks.
    
    #TODO:
        * finish screenshot logging
    '''

    class Url(object):
        '''A url object that can be compared with other url orbjects
        without regard to the vagaries of encoding, escaping, and ordering
        of parameters in query strings.
        from http://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
        '''

        def __init__(self, url):
            parts = urlparse.urlparse(url)
            _query = frozenset(urlparse.parse_qsl(parts.query))
            _path = urllib.unquote_plus(parts.path)
            parts = parts._replace(query=_query, path=_path)
            self.parts = parts

        def __eq__(self, other):
            return self.parts == other.parts

        def __hash__(self):
            return hash(self.parts)

    def __init__(self, base_url, webdriver, logger, settings={}):
        self._init_webdriver(base_url, webdriver, settings=settings)
        self.log = logger or Logger(self.__class__.__name__)

    def _init_webdriver(self, base_url, webdriver, settings={}):
        assert webdriver, 'You must provide a webdriver'
        self._driver = webdriver
        self.settings = settings
        # Initialize values
        self._base_url = base_url
        self._wait_timeout = self.settings.get('wait_timeout', 2)
        
    def _decorate_exc_sshot(self, meth_filter=None):
        fltr = lambda n, method:  (getattr(method, _with_screenshot, False)
                                   or n.startswith('test'))
        meth_filter = meth_filter or fltr
        self._sshot_lock = Lock()
        for name, method in inspect.getmembers(self):
            if not (isinstance(method, MethodType)
            and getattr(method, _with_screenshot, True)):
                continue
            if getattr(method, _zero_screenshot, False):
                method = self._decorate(name, method, zero_screeshot=True)
                setattr(self, name, method)
            elif(name != 'screenshot' 
                and meth_filter(name, method)):
                self.log.debug('Decorating %r for screenshot' % name)
                method = self._decorate(name, method)
                setattr(self, name, method) 
                
    def _decorate(self, name, method, zero_screeshot=False):
        if not zero_screeshot:
            @wraps(method)
            def dec(*args, **kwargs):
                try:
                    return method(*args, **kwargs)
                except Exception as e:
                    if self._sshot_lock.acquire(False):
                        self._exception_screenshot(name, e)
                        self._sshot_lock.release()
                    raise
        else:
            @wraps(method)
            def dec(*args, **kwargs):
                #block any further exception screenshot, until
                #we return from this call
                locked = self._sshot_lock.acquire(False)
                try:
                    return method(*args, **kwargs)
                finally:
                    if locked:
                        self._sshot_lock.release()
        return dec

    def _quit_webdriver(self):
        self._driver.quit()
        self._driver = None

    def get_driver(self):
        assert self._driver, 'driver was not initialized'
        return self._driver
    
    def _string_to_filename(self, str_, max_size=150):
        '''
        For example:
          'My Super Company' into 'my_super_company'
        It will became like a python variable name, although it will accept 
          starting with a number
        2-Will collect alphanumeric characters and ignore the rest
        3-Will join collected groups of alphanumeric characters with "_"
        :param str_:
        '''
        str_ = str_.strip()
        words = re.findall(r'[a-zA-Z0-9][a-zA-Z0-9]*', str_)
        str_ = '_'.join(words)
        if max_size:
            return str_[:max_size]
        else:
            return str_

    _exc_sshot_count = 0
    def _exception_screenshot(self, name, exc):
        self._exc_sshot_count += 1
        dr = self.get_driver()
        exc = self._string_to_filename(repr(exc))
        count = self._exc_sshot_count
        test = self.__class__.__name__
        filename = '{count:03d}.{test}.{name}.{exc}.png'.format(**locals())
        self.log.e('Saving exception screenshot to: %r' % filename)
        exc_dir = self.settings.get('screenshot_exceptions_dir')
        dr.save_screenshot(os.path.join(exc_dir, filename))
        return filename

    _quick_sshot_count = 0
    def _quick_screenshot(self):
        self._quick_sshot_count += 1
        filename = '{count:03d}.quick_screenshot.png'.format(**locals())
        self.log.i('Saving exception screenshot to: %r' % filename)
        self.get_driver().save_screenshot(filename)        

    def screenshot(self, *args, **kwargs):
        #self.log.w('WebdriverUtils.screenshot not yet implemented.')
        pass
    
    def assert_screenshot(self, name, valid=None):
        #self.log.w('WebdriverUtils.assert_screenshot not yet implemented.')
        pass

    def current_path(self):
        return urlparse.urlparse(self.current_url()).path

    def current_url(self):
        return self.get_driver().current_url

    def build_url(self, path):
        return urlparse.urljoin(self._base_url, path)

    def url_equals(self, url_a, url_b):
        return self.Url(url_a) == self.Url(url_b)

    def path_equals(self, path_a, path_b):
        clean = lambda p: urllib.unquote_plus(p.strip('/'))
        return clean(path_a) == clean(path_b)

    def get_page(self, path, base=None, check_load=False, condition=None):
        #default value
        base = base if base else self._base_url
        driver = self.get_driver()
        url = self.build_url(path)
        if url.startswith('https') and isinstance(driver, webdriver.PhantomJS):
            self.log.d('PhantomJS may fail with https if you don\'t pass '
                       'service_args=[\'--ignore-ssl-errors=true\']' 
                       ' Trying to fetch {url!r}'.format(url=url))
        self.log.d('Fetching page at {url!r}'.format(url=url))
        driver.get(url)
        #Errors
        msg = 'Couldn\'t load page at {url!r}'.format(url=url)
        if check_load and not self.wait_condition(condition):
            raise LookupError(msg)
        if driver.current_url == u'about:blank':
            raise LookupError(msg + '. Url is u"about:blank"')
        if not self.url_equals(url, driver.current_url):
            self.log.d('Fetching {url!r} and we got {driver.current_url!r}.'
                       .format(**locals()))
        return driver

    def get_page_once(self, path, base=None, check_load=False, condition=None):
        driver = self.get_driver()
        if not self.url_equals(self.build_url(path), driver.current_url):
            return self.get_page(path, base, check_load, condition)
        return driver

    _max_wait = 2
    _default_condition = 'return "complete" == document.readyState;'
    def wait_condition(self, condition=None, max_wait=None, print_msg=True):
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
        max_wait = max_wait or self._max_wait
        top = int(parts * max_wait)
        for i in range(1, top+1):
            loaded = condtn(self.get_driver())
            if loaded:
                self.log.d('Condition "%s" is True.' % condition)
                break
            self.log.d('Waiting condition "%s" to be True.' % condition)
            time.sleep(float(i)/parts)
        if not loaded and print_msg:
            msg = ('Page took too long to load. Increase max_wait (secs) class'
                   ' attr. Or override _wait_script method.')
            self.log.d(msg)
        return loaded
    
    def _get_xpath_script(self, xpath, single=True):
        common_func = '''
function extract_elem(elem){
    var elem = elem
    //elem.noteType == 1 //web element
    if(elem.nodeType == 2){
      //attribute
      elem = elem.value;
    }
    if(elem.nodeType == 3){
      //text()
      elem = elem.wholeText;
    }
    return elem;
}
        '''
        if single:
            script_single = '''
var xpath = %(xpath)r;
//XPathResult.FIRST_ORDERED_NODE_TYPE = 9
var e = document.evaluate(xpath, document, null,9, null).singleNodeValue;
return extract_elem(e);
            '''
        else:
            script_list = '''
var xpath = %(xpath)r;
//XPathResult.ORDERED_NODE_ITERATOR_TYPE = 5
var es = document.evaluate(xpath, document, null, 5, null);
var r = es.iterateNext();
var eslist = [];
while(r){
    eslist.push(extract_elem(r));
    r = es.iterateNext();
}
return eslist;
        '''
        script = script_single if single else script_list
        return common_func + script % locals()

    def select_xpath(self, xpath, single=True):
        dr = self.get_driver()
        try:
            e = dr.execute_script(self._get_xpath_script(xpath, single))
        except WebDriverException as e:
            msg = ('WebDriverException: Could not select xpath {xpath!r} '
                'for page {dr.current_url!r}\n Error:\n {e}'.format(**locals()))
            raise LookupError(msg)
        return e

    def has_xpath(self, xpath):
        try:
            self.select_xpath(xpath)
            return True
        except LookupError:
            return False

    def extract_xpath(self, xpath, single=True):
        result = self.select_xpath(xpath, single)
        if isinstance(result, WebElement):
            result = result.text
        if single:
            assert isinstance(result, basestring)
        else:
            assert not any(not isinstance(s, basestring) for s in result)
        return result

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
        
    def wait(self, timeout=None):
        time.sleep(timeout or self._wait_timeout)



def smoke_test_module():
    class WDU(WebdriverUtils):
        def __init__(self, base):
            self.log = Logger(self.__class__.__name__)
            self._decorate_exc_sshot()
            
        def get_driver(self, *args, **kwargs):
            class Driver(object):
                def save_screenshot(self, path):
                    print('Would save to: %r' % path)
            return Driver()

        @zero_screenshot
        def extract_xpath(self, xpath, ret='text'):
            self.select_xpath(xpath, ret)
        
        @screenshot
        def _example(self, bar):
            try:
                self.select_xpath(bar)
            finally:
                raise LookupError('With screenshot')

        def _example2(self, bar):
            raise LookupError('Without screenshot')        
        

        def _example3(self, bar):
            try:
                self.select_xpath(bar)
            finally:
                raise LookupError('Without screenshot')        

        @no_screenshot
        def example4(self, bar):
            try:
                self.select_xpath(bar)
            finally:
                raise LookupError('Without screenshot')        

        
    wdu = WDU('http://www.juju.com/', 
             #browser='Chrome'
             )
    #wdu.get_page('/')
    #import traceback
    for m in [
            wdu.select_xpath, #select_xpath
            wdu.extract_xpath, 
            wdu._example,  #select_xpath + _example
            wdu._example2, 
            wdu._example3, #select_xpath
            wdu.example4, #select_xpath
              ]:            
        try:
            m('bar')
        except Exception as e:
            pass
            #traceback.print_exc()

if __name__ == "__main__":
    smoke_test_module()

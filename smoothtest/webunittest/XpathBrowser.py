# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2015 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import urlparse
import time
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.common.exceptions import WebDriverException,\
    TimeoutException
from smoothtest.Logger import Logger
import urllib
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions


class Url(object):

    '''A url object that can be compared with other url orbjects
    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings.
    from http://stackoverflow.com/questions/5371992/comparing-two-urls-in-python
    '''

    def __init__(self, url):
        if not isinstance(url, Url):
            self._orig = parts = urlparse.urlparse(url)
            _query = frozenset(urlparse.parse_qsl(parts.query))
            _path = urllib.unquote_plus(parts.path).rstrip('/')
            parts = parts._replace(query=_query, path=_path)
            self.parts = parts
        else:
            self._orig = url._orig
            self.parts = url.parts

    def get_original(self):
        '''
        Get original url.
        '''
        return urlparse.urlunparse(self._orig)

    def get_path_and_on(self):
        '''
        Get (path + params + query + fragment) as string from original url.
        '''
        return urlparse.urlunparse(self._orig._replace(scheme='', netloc=''))

    def cmp_path(self, url):
        url = self._convert(url)
        return self.get_path_and_on() == url.get_path_and_on()

    @staticmethod
    def are_equal(url_a, url_b):
        return Url(url_a) == Url(url_b)

    def __eq__(self, other):
        other = self._convert(other)
        return self.parts == other.parts

    def _convert(self, url):
        if isinstance(url, basestring):
            url = Url(url)
        return url

    def __hash__(self):
        return hash(self.parts)


class XpathBrowser(object):
    '''
    Class for making Webdriver more xpath-friendly.
    This class is designed to be framework independent, to be reused by other
    testing frameworks.
    '''
    Url = Url

    def __init__(self, base_url, webdriver, logger=None, settings=None):
        '''
        :param base_url: common base url (e.g: http://example.com, http://example.com/some/common/path) 
            Used to build URL for all methods accepting the "path" argument. 
        :param webdriver: selenium's webdriver object (connected to Firefox, Chrome, etc...)
        :param logger: You can optionally pass a smoothtest.Logger instance (or a child class's instance)  
        :param settings: smoothtest settings object.
        '''
        self.log = logger or Logger(self.__class__.__name__)
        assert webdriver, 'You must provide a webdriver'
        self._driver = webdriver
        self.settings = settings or {}
        # Initialize values
        self._base_url = base_url
        self._wait_timeout = self.settings.get('wait_timeout', 2)

    def set_base_url(self, base_url):
        '''
        Set base URL. (in order to build full URLs passing only paths)

        :param base_url: base URL string eg:"http://example.com/". 
            You can even  add more details after the host like:"http://example.com/common_path/" 
        '''
        self._base_url = base_url

    def _quit_webdriver(self):
        '''
        Quit selenium's webdriver.
        '''
        self._driver.quit()
        self._driver = None

    def get_driver(self):
        '''
        Return selenium's webdriver instance
        '''
        assert self._driver, 'driver was not initialized'
        return self._driver

    def current_path(self):
        '''
        Get (path + params + query + fragment) as string from current url.
        '''
        return self.Url(self.current_url()).get_path_and_on()

    def current_url(self):
        '''
        Return the current page's URL. (from webdriver instance) 
        '''
        return self.get_driver().current_url

    def build_url(self, path):
        '''
        Build a full URL from a URL path (path and on)
        
        :param path: path and on eg:"/blog/123?param=1"
        '''
        assert self._base_url, 'No base_url set for building urls'
        return urlparse.urljoin(self._base_url, path)

    def get_url(self, url, condition=None):
        '''
        Open a page in the browser controlled by webdriver.
        
        :param path: full URL of the page
        :param condition: condition script or functor passed to the `wait_condition` method
        '''
        driver = self.get_driver()
        if url.startswith('https') and isinstance(driver, webdriver.PhantomJS):
            self.log.d('PhantomJS may fail with https if you don\'t pass '
                       'service_args=[\'--ignore-ssl-errors=true\']'
                       ' Trying to fetch {url!r}'.format(url=url))
        self.log.d('Fetching page at {url!r}'.format(url=url))
        driver.get(url)
        # Errors
        msg = 'Couldn\'t load page at {url!r}'.format(url=url)
        if condition and not self.wait_condition(condition):
            raise LookupError(msg)
        if self.current_url() == u'about:blank':
            raise LookupError(msg + '. Url is u"about:blank"')
        if not self.Url.are_equal(url, self.current_url()):
            self.log.d('For {url!r} we got {current!r}.'
                       .format(url=url, current=self.current_url()))

    def get_page(self, path, condition=None):
        '''
        Open a page in the browser controlled by webdriver.
        
        :param path: path and on eg:"/blog/123?param=1" to get the page from
        :param condition: condition script or functor passed to the `wait_condition` method
        '''
        self.get_url(self.build_url(path), condition)

    def get_page_once(self, path, condition=None):
        '''
        Open a page only once in the browser controlled by webdriver.
        If the page is already opened, then no reloading is performed.
        Beware: if a page implies redirection, it will be reloaded anyway.
        (becaus URL changes and it does not match the value of `path`)
        
        :param path: path and on eg:"/blog/123?param=1" to get the page from
        :param condition: condition script or functor passed to the `wait_condition` method
        '''
        # Remove user credentials (they are not shown in browser)
        url = self.build_url(path)
        parts = urlparse.urlparse(self.build_url(path))
        if '@' in parts.netloc:
            netloc = parts.netloc.split('@')[1]
            url = urlparse.urlunparse(parts._replace(netloc=netloc))
        # Check if page was already loaded
        if not self.Url.are_equal(url, self.current_url()):
            # Url is different, load new page
            self.get_page(path, condition)
        else:
            # Page already loaded
            self.log.d('Page already loaded once: %r' % url)

    _max_wait = 2
    _default_condition = 'return "complete" == document.readyState;'

    def wait_condition(self, condition=None, max_wait=None, print_msg=True):
        '''
        Active wait (polling) function, for a specific condition inside a page.
        
        Condition may be:
          - a functor: a function receiving this xbrowser object as argument
            returns True if condition was met, eg:

            def condition(xbrowser):
               # We want to know if the email was loaded
               return xbrowser.extract_xsingle('//a[@id="EmailSubject"]') == u'Welcome to our service'

          - a string javascript function, eg:
            """
            return "complete" == document.readyState;
            """

            The javascript must have the return statement at the end,
            which must be True if the condition is met
            
        If you don't supply any condition, then this default javascript condition
        will be used:
            return "complete" == document.readyState;
            
        Sometimes that condition is not good enough, so you may use a python
        function or a javascript condition to be sure you got the page/result
        loaded.

        :param condition: functor or javascript string of condition checking logic.
        :param max_wait: Max amount of time to wait for condition to be true.
        :param print_msg: print debug message (debugging purpose)
        '''
        condition = condition if condition else self._default_condition
        if isinstance(condition, basestring):
            # Its a javascript script
            def condition_func(xbrowser):
                return xbrowser.get_driver().execute_script(condition)
            condtn = condition_func
        else:
            condtn = condition
        # first start waiting a tenth of the max time
        # then increase time adding a tenth until getting the 100% of wait time
        parts = 10
        max_wait = max_wait or self._max_wait
        top = int(parts * max_wait)
        for i in range(1, top + 1):
            loaded = condtn(self)
            if loaded:
                self.log.d('Condition "%s" is True.' % condition)
                break
            self.log.d('Waiting condition "%s" to be True.' % condition)
            time.sleep(float(i) / parts)
        # If condition was not satisfied print debug message
        if not loaded and print_msg:
            msg = ('Page took too long to load. Increase max_wait (secs) class'
                   ' attr. Or override _wait_script method.')
            self.log.d(msg)
        # Return whether condition was satisfied
        return loaded

    def _get_xpath_script(self, xpath, single=True):
        '''
        Get Javascript code for getting single or multiple nodes from webdriver
        page's DOM.
        Returns [web weblement, attribute, text] depending o the xpath specified.

        :param xpath: xpath to build the script from
        :param single: select only a single node
        '''
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
        script_single = '''
var xpath = %(xpath)r;
//XPathResult.FIRST_ORDERED_NODE_TYPE = 9
var e = document.evaluate(xpath, document, null,9, null).singleNodeValue;
return extract_elem(e);
            '''
        script_multiple = '''
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
        script = script_single if single else script_multiple
        return common_func + script % locals()

    def select_xpath(self, xpath):
        '''
        Select HTML nodes given an xpath.
        May return:
            - webdriver's web element
            - strings (if xpath specifies @attribute or text()) 
        
        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        :returns: list of selected Webelements or strings
        
        '''
        return self._select_xpath(xpath, single=False)

    def select_xsingle(self, xpath):
        '''
        Select first node specified by xpath.
        If xpath is empty, it will raise an exception

        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        :returns: Webelement or string (depeding on the passed xpath)
        '''
        return self._select_xpath(xpath, single=True)

    def _select_xpath(self, xpath, single):
        '''
        Select nodes specified by xpath
        
        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        :param single: if True, returns only the first node
        '''
        dr = self.get_driver()
        try:
            e = dr.execute_script(self._get_xpath_script(xpath, single))
        except WebDriverException as e:
            msg = (
                'WebDriverException: Could not select xpath {xpath!r} '
                'for page {dr.current_url!r}\n Error:\n {e}'.format(
                    **locals()))
            raise LookupError(msg)
        return e

    def has_xpath(self, xpath):
        '''
        Returns True if xpath is present (won't check if it has content)

        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        '''
        return self._has_xpath(xpath, single=False)

    def has_xsingle(self, xpath):
        '''
        Returns True if xpath is present AND there is at least 1 
        node in the resulting selection.

        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        '''
        return self._has_xpath(xpath, single=True)

    def _has_xpath(self, xpath, single):
        '''
        Returns True if xpath exists. 
        
        :param xpath: xpath's string eg:"/div[@id='example']/text()"
        :param single: if True, it makes sure there is at least 1 node in the
            xpath selection.
        '''
        try:
            self._extract_xpath(xpath, single)
            return True
        except LookupError:
            return False

    def extract_xpath(self, xpath):
        '''
        DEPRECATED: prefer select_xpath + /text() instead
        
        Extract text inside xpath result.
        No need to pass '../text()'
        
        :param xpath: xpath's string eg:"/div[@id='example']"
        :returns: list of extracted strings
        '''
        return self._extract_xpath(xpath, single=False)

    def extract_xsingle(self, xpath):
        '''
        DEPRECATED: prefer select_xsingle + /text() instead

        Extract text of the first node inside xpath.
        No need to pass '../text()'
        
        :param xpath: xpath's string eg:"/div[@id='example']"
        :returns: extracted string
        '''
        return self._extract_xpath(xpath, single=True)

    def _extract_xpath(self, xpath, single):
        self.log.w('This method is deprecated. Use instead select_xpath or'
                   ' select_xsingle + "/text()" in the xpath')
        result = self._select_xpath(xpath, single)
        def extract(result):
            if isinstance(result, WebElement):
                return result.text
            return result
        result = extract(result)
        if isinstance(result, list):
            result = [extract(e) for e in result]
        # Check consistency (all must be basestring)
        if single:
            assert isinstance(result, basestring)
        else:
            assert not any(not isinstance(s, basestring) for s in result)
        return result

    def fill(self, xpath, value):
        '''
        Fill input field on page:
          - selects Webelement
          - sends keystroke to it

        :param xpath: xpath's string eg:"./input[@id='example']"
        :param value: string to fill the input with
        '''
        e = self.select_xsingle(xpath)
        e.clear()
        e.send_keys(value)

    def click(self, xpath):
        '''
        Click element in xpath:
          - selects Webelement
          - sends click to it

        :param xpath: xpath's string eg:"./button[@id='send_form']"
        '''
        e = self.select_xsingle(xpath)
        e.click()

    def wait(self, timeout=None):
        '''
        Useful wait method (alias to time.sleep)
        The timeout can be set globally or passed to the method.

        :param timeout: if specified, amount of seconds to wait. (else use global value)
        '''
        time.sleep(timeout or self._wait_timeout)

    def wipe_alerts(self, timeout=0.5):
        '''
        Wipe browser's alert dialogs. Useful for unblocking webdriver. 
        (Although using alert dialogs in a webpage is not recommended)

        :param timeout: max wait for alert in second (default=0.5)
        '''
        try:
            WebDriverWait(self.get_driver(), timeout
                          ).until(expected_conditions.alert_is_present(),
                                  'Timed out waiting alert.')
            alert = self.get_driver().switch_to_alert()
            alert.accept()
        except TimeoutException:
            pass

    _quick_sshot_count = 0

    def quick_screenshot(self):
        '''
        Take a quick screenshot saving the file to the current dir.
        It will autonumerate screenshots. 001.quick_screenshot.png ...etc
        '''
        self._quick_sshot_count += 1
        filename = '{count:03d}.quick_screenshot.png'.format(**locals())
        self.log.i('Saving screenshot to: %r' % filename)
        self.save_screenshot(filename)

    def save_screenshot(self, filename):
        '''
        Take a screenshot and save it to the path specified in filename
        :param filename: path to save the screenshot file to
        '''
        self.get_driver().save_screenshot(filename)

    def execute_script(self, script, *args):
        '''
        Execute javascript in the Browser.
        Will return a value if the specified script returns a value.
        :param script: javascript script to be executed. 
        '''
        return self.get_driver().execute_script(script, *args)

    def fill_form(self, **inputs):
        '''
        Fill a form given a {<input/textarea name>:<value>} dictionary
        Example:
            browser.fill_form(name='John', surname='Doe', email='john.doe@gmail.com')
        Is equivalent to doing:
            browser.fill_form_xpath({'//input[@name="name"] | //textarea[@name="name"]':'John', ...})
        :param inputs: kwargs dictionary of <form's field name>=<value>
        '''
        self.fill_form_attr('name', inputs)

    def fill_form_attr(self, attr, inputs):
        '''
        :param attr: attribute name to solve xpaths with
        :param inputs: dictionary of {<form's field attr value>:<value to enter>}
        '''
        xpath = '//input[@{0}={1!r}] | //textarea[@{0}={1!r}]'
        inputs = {xpath.format(attr,name):value
                  for name, value in inputs.iteritems()}
        self.fill_form_xpath(inputs)

    def fill_form_xpath(self, inputs):
        '''
        :param inputs: dictionary of {<form's field xpath>:<value to enter>}
        '''
        for xpath, value in inputs.iteritems():
            self.fill(xpath, value)

    def fill_form_ordered(self, items, attr='name'):
        '''
        Fill a form given a [(<input/textarea name>,<value>),...] list
        :param items: list of [(name, value), ...]
        '''
        for name, value in items:
            self.fill('//input[@{0}={1!r}] | //textarea[@{0}={1!r}]'
                      .format(attr, name), value)


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


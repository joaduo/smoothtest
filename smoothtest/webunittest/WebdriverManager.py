'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.base import SmoothTestBase
from selenium import webdriver
from pyvirtualdisplay import Display
from smoothtest.singleton_decorator import singleton_decorator
from contextlib import contextmanager
from collections import defaultdict

def new_webdriver(browser=None, *args, **kwargs):
    return WebdriverManager().new_webdriver(browser, *args, **kwargs)


def stop_display():
    return WebdriverManager().stop_display()


@singleton_decorator
class WebdriverManager(SmoothTestBase):

    def __init__(self):
        self._locked = {}
        self._released = defaultdict(list)
        self._virtual_display = None

    @contextmanager
    def get_webdriver(self, browser=None, keep=True):
        wdriver = self._get_webdriver(browser)
        try:
            yield wdriver
        except:
            raise
        finally:
            self.release_webdriver(wdriver, keep)

    def release_webdriver(self, wdriver, keep=True):
        assert wdriver in self._locked, 'Webdriver %r was never locked' % wdriver
        browser = self._locked[wdriver]
        del self._locked[wdriver]
        if keep:
            self._released[browser].append(wdriver)
        else:
            wdriver.close()
    
    def new_webdriver(self, browser):
        if not self.global_settings.get('webdriver_pooling'):
            self.close_webdrivers()
        browser = self._get_full_name(browser)
        if self._released.get(browser):
            wdriver = self._released[browser].pop()
        else:
            wdriver = self._new_webdriver(browser)
        self._locked[wdriver] = browser
        return wdriver

    def _new_webdriver(self, browser=None, *args, **kwargs):
        browser = self._get_full_name(browser)
        # Setup display before creating the browser
        self.setup_display()
        if browser == 'PhantomJS':
            kwargs.update(service_args=['--ignore-ssl-errors=true'])
        if browser == 'Firefox'\
        and self.global_settings.get('webdriver_firefox_profile'):
            fp = webdriver.FirefoxProfile(self.global_settings.get('webdriver_firefox_profile'))
            driver = webdriver.Firefox(fp)
        else:
            driver = getattr(webdriver, browser)(*args, **kwargs)
        return driver

    def close_webdrivers(self):
        all_wdrivers = self._locked.keys() + reduce(lambda x,y: y+x, self._released.values(), [])
        for w in all_wdrivers:
            try:
                w.close()
            except Exception as e:
                self.log.w('Ignoring %r:%s' % (e,e))
        self._locked.clear()
        self._released.clear()

    def setup_display(self):
        '''
        Create virtual display if set by configuration
        '''
        def get(name, default=None):
            return self.global_settings.get('virtual_display_' + name, default)
        if not get('enable'):
            if self._virtual_display:
                self.log.w('There is a display enabled although config says'
                           ' different')
            return
        elif self._virtual_display:
            # There is a display configured
            return
        # We need to setup a new virtual display
        d = Display(size=get('size', (800, 600)), visible=get('visible'))
        d.start()
        self._virtual_display = d

    def stop_display(self):
        '''
        Convenient function to stop the virtual display
        '''
        # Nice alias
        display = self._virtual_display
        if ((not self.global_settings.get('virtual_display_keep_open')
             or not self.global_settings.get('virtual_display_visible'))
                and display):
            self.log.d('Stopping virtual display %r' % display)
            display.stop()
            WebdriverManager._virtual_display = None

    def _get_full_name(self, browser=None):
        # Solve name based on first character (easier to specify by the user)
        browser = (
            browser if browser else self.global_settings.get(
                'webdriver_browser',
                'Firefox'))
        # Select based in first letter
        # TODO: add IE and Opera
        char_browser = dict(f='Firefox',
                            c='Chrome',
                            p='PhantomJS',
                            )
        char = browser.lower()[0]
        assert char in char_browser, 'Could not find browser %r' % browser
        return char_browser.get(char)


def smoke_test_module():
    mngr = WebdriverManager()
    ffox = mngr.new_webdriver('Firefox')
    ffox.quit()
    mngr.stop_display()
    with mngr.get_webdriver('f') as ffox2:
        print ffox2
    mngr.close_webdrivers()


if __name__ == "__main__":
    smoke_test_module()

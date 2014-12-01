'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.base import SmoothTestBase
from selenium import webdriver
from pyvirtualdisplay import Display


def new_webdriver(browser=None, *args, **kwargs):
    return WebdriverManager().new_webdriver(browser, *args, **kwargs)


def stop_display():
    return WebdriverManager().stop_display()


class WebdriverManager(SmoothTestBase):
    # class' variable to share the display object
    default_display = None
    
    def new_webdriver(self, browser=None, *args, **kwargs):
        browser = self._get_full_name(browser)
        # Setup display before creating the browser
        self.setup_display()
        if browser == 'PhantomJS':
            kwargs.update(service_args=['--ignore-ssl-errors=true'])
        driver = getattr(webdriver, browser)(*args, **kwargs)
        return driver
    
    def setup_display(self):
        '''
        Create virtual display if set by configuration
        '''
        def get(name, default=None):
            return self.global_settings.get('virtual_display_' + name, default)
        if not get('enable'):
            if WebdriverManager.default_display:
                self.log.w('There is a display enabled although config says'
                           ' different')
            return
        elif WebdriverManager.default_display:
            # There is a display configured
            return
        # We need to setup a new virtual display
        d = Display(size=get('size',(800,600)), visible=get('visible'))
        d.start()
        WebdriverManager.default_display = d
        
    def stop_display(self):
        '''
        Convenient function to stop the virtual display
        '''
        # Nice alias
        display = WebdriverManager.default_display
        if ((not self.global_settings.get('virtual_display_keep_open')
             or not self.global_settings.get('virtual_display_visible'))
            and display):
            self.log.d('Stopping virtual display %r' % display)
            display.stop()
            WebdriverManager.default_display = None

    def _get_full_name(self, browser=None):
        # Solve name based on first character (easier to specify by the user) 
        browser = (browser if browser 
                   else self.global_settings.get('webdriver_browser', 'Firefox'))        
        # Select based in first letter
        #TODO: add IE and Opera
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


if __name__ == "__main__":
    smoke_test_module()

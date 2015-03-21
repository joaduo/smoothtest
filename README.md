# SmoothTest

[ ![Codeship Status for joaduo/smoothtest](https://codeship.com/projects/cdad4830-b21d-0132-82c3-62decd5a7cb3/status?branch=master)](https://codeship.com/projects/69981)

General purpose Testing Utilities and also special testing tools for Web Applications

## Better API for accessing Selenium

With smoothtest you can write nicer tests for web sites.

```python
class Home(TestCaseBase):

    _tested_page = '/'

    def test_home(self):
        self.get_page(self._tested_page)
        self.assert_text('//p[@id="msg"]', u'Sign up to request beta access.')
        
    def test_empty_email(self):
        self.get_page(self._tested_page)
        self.click('//a[@class="new_job tab_link"]')
        class_ = self.extract_xpath('//input[@name="email"]/@class')
        self.assertTrue('error' in class_.split(), 'No error style applied')

```

The API is very XPath oriented, so you can test your XPath with Firefox's extensions like FirePath.

## How to use smoothtest

The main utility is the `autotest` command. This command monitors your project's files and you unittest files for changes, it will trigger reloading and rerunning tests when a file changes. This means you can work in your code and see how tests are affected automatically. You can select a group of tests files to be monitored - that trigger partial reloads of those same modules -  and an group of files or directories to trigger full reloads of the project.

It also provides a ipython UI interface to modify certain values and re-test.

Do
```
python -m smoothtest.autotest.Command
```
To enter the Ipython UI without specifying any initial test.

If you want to start with a specific test, run this to get possible arguments.
```
python -m smoothtest.autotest.Command --help
```

Inside Ipython you you have to commands
```
%autotest
%test
``` 
Where `%autotest` has same parameters as the `python -m smoothtest.autotest.Command` command but adds `-u` for updating test parameters and `-f` for forcing a reloading.

Autotest command is still in beta stage, so some functionality won't be as reliable as expected. (but still useful for developing tests) You may need to restart the autotest command from time to time.

## Configuration

You will need a `smoothtest_settings.py` in your `PYTHONPATH` that looks like this:

``` 
from smoothtest.settings.default import DefaultSettings
import logging

class Settings(DefaultSettings):
    web_server_url = 'http://localhost:8011/'

    webdriver_browser = 'Firefox' #'Chrome' 'PhantomJS'
    webdriver_pooling = True
    webdriver_inmortal_pooling = True
    webdriver_keep_open = False
    webdriver_log_level = logging.WARNING
``` 

## Installing
You can use pip to install it:
```
pip install smoothtest 
``` 
Or uninstall it:
```
pip uninstall smoothtest 
``` 

## Windows and Mac OSX

I tested Smoothtest under Linux, although it was designed to be multiplatform I still haven't fully tested outside Linux.

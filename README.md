# SmoothTest

[ ![Codeship Status for joaduo/smoothtest](https://codeship.com/projects/cdad4830-b21d-0132-82c3-62decd5a7cb3/status?branch=master)](https://codeship.com/projects/69981)

General purpose Testing Utilities and also special testing tools for Web Applications

## Better API for accessing Selenium

With smoothtest you can write nicer tests for web sites.

```python
class SearchEnginesDemo(unittest.TestCase):
    def setUp(self):
        # We need to enter "single test level" of life for each test
        # It will initialize the webdriver if no webdriver is present from upper levels
        self._level_mngr = WebdriverManager().enter_level(level=SINGLE_TEST_LIFE)
        # Get Xpath browser
        self.browser = self._level_mngr.get_xpathbrowser(name=__name__)

    def tearDown(self):
        # Make sure we quit those webdrivers created in this specific level of life
        self._level_mngr.exit_level()

    def test_duckduckgo(self):
        # Load a local page for the demo
        self.browser.get_url('https://duckduckgo.com/')
        # Type smoothtest and press enter
        self.browser.fill(".//*[@id='search_form_input_homepage']", 'smoothtest\n')
        result_link = './/a[@title="smoothtest "]'
        # Wait for the result to be available
        self.browser.wait_condition(lambda brw: brw.select_xpath(result_link))
        # Click on result
        self.browser.click(result_link)
        # First result should point to github
        expected_url = 'https://github.com/joaduo/smoothtest'
        wait_url = lambda brw: brw.current_url() == expected_url
        # Make sure we end up in the right url
        self.assertTrue(self.browser.wait_condition(wait_url))

```

The API is very XPath oriented, so you can test your XPath with Firefox's extensions like FirePath.

## How to use smoothtest

The main utility is the `smoothtest` command. This command monitors your project's files and your unittest files for changes, it will trigger reloading and rerunning tests when a file changes. This means you can work in your code and see how tests are affected automatically. You can select a group of tests files to be monitored - that trigger partial reloads of those same modules -  and an group of files or directories to trigger full reloads of the project.

It also provides a ipython UI interface to modify certain values and re-test.

Do
```
smoothtest
```
To enter the Ipython UI without specifying any initial test.

If you want to start with a specific test, run this to get possible arguments.
```
smoothtest --help
```

Inside Ipython you you have to commands
```
%smoothtest
%test
%reset
%test_config
%get
%chrome
%firefox
%phantonjs
%steal_xpathbrowser
``` 
Where `%smoothtest` has same parameters as the `smoothtest` command but adds `-u` for updating test parameters and `-f` for forcing a reloading.

`smoothtest` command is still in beta stage, so some functionality won't be as reliable as expected. (but still useful for developing tests) You may need to restart the `smoothtest` command from time to time.

## Configuration

You will need a `smoothtest_settings.py` in your `PYTHONPATH` that looks like this:

``` 
from smoothtest.settings.default import DefaultSettings
import logging

class Settings(DefaultSettings):
    web_server_url = 'http://localhost:8011/'

    webdriver_browser = 'Firefox' #'Chrome' 'PhantomJS'
    ...
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

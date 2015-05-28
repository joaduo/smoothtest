# Autotest Guide

## Software requirements

Ipython... etc TODO
PhantomJS

## Configuring Smoothtest

## Tutorial: Working with the bundled demo

### Starting autotest

 1. In a terminal, start an autotest shell with the bundled demo like:
	```
	python -m smoothtest.autotest.Command --smoothtest-settings settings.py  -t smoothtest/demos/xpath_browser_demo.py
	```
	
	If you are using Firefox as browser in configuration, a Firefox browser should be open with the demo page display a "Loren Ipsum" text. 
	Also, in the terminal, you will see something like the following output: 
	```
	[Master] 21:02:16: Closing stdin
	[Master] 21:02:16: Forked process callback starting...
	[Master] 21:02:16: Watching file 'smoothtest/demos/xpath_browser_demo.py'
	[TestRunner] 21:02:16: Closing stdin
	[Master] 21:02:16: Partial reload for: ['smoothtest.demos.xpath_browser_demo.TestXpathBrowser.test_demo']. Triggered by 'First test after setup'
	[TestRunner] 21:02:16: Forked process callback starting...
	[Master] 21:02:16: Starting observer for:
	  ['smoothtest/demos/xpath_browser_demo.py']
	  []
	[Master] 21:02:16: Receiving command: AutotestCmd(cmd='get_subprocess_pid', args=(), kwargs={})
	[Master] 21:02:16: Answering [AutotestAnswer(sent_cmd=AutotestCmd(cmd='get_subprocess_pid', args=(), kwargs={}), result=18881, error=None)]
	[TestRunner] 21:02:16: Receiving command: AutotestCmd(cmd='test', args=(set(['smoothtest.demos.xpath_browser_demo.TestXpathBrowser.test_demo']), [], None), kwargs={})
	[TestRunner] 21:02:16: Fetching page at 'file:///home/jduo/000-JujuUnencrypted/EclipseProjects/smoothtest/smoothtest/smoothtest/demos/html/xpath_browser_demo.html'
	
	In [1]: .
	----------------------------------------------------------------------
	Ran 1 test in 0.636s
	
	OK
	[TestRunner] 21:02:17: Answering [AutotestAnswer(sent_cmd=AutotestCmd(cmd='test', args=(set(['smoothtest.demos.xpath_browser_demo.TestXpathBrowser.test_demo']), [], None), kwargs={}), result=<smoothtest.TestResults.TestResults object at 0x7f6ba1a88210>, error=None)]
	[Master] 21:02:17: Received TestRunner's answer: EXCEPTIONS=0 FAILURES=0 ERRORS=0 from TOTAL=1
	```
	
	Most important line is **[Master] 21:02:17: Received TestRunner's answer: EXCEPTIONS=0 FAILURES=0 ERRORS=0 from TOTAL=1** saying the tests were successful. 
	
	_**Note**: Since there are three processes attached to the terminal (named Main, Master and TestRunner) they will overlap the ipython shell output. So press enter once and you will get a_ 

 2. You can trigger a new test round executing in the shell: `%test`
 
 3. You can also trigger a new test round if you edit something inside `xpath_browser_demo.py` file. 
   a. If you add or delete any `test_*` method, you will see the errors on the terminal while tests are triggered. This is not a problem since we can add and remove test methods from the shell. (we will see how to do it later)
 
   b. You can also close the browser and it will be re-launched when doing `%test`. (you will see a warning about the missing browser)
   
   c. You can change the current brower executing: `%firefox`, `%chrome` or `%phantomjs`. Each time you specify a browser a test round is triggered.

 4. Exit the shell. You can exit the shell as a normal ipython shell. (CTRL+D, quit, exit...)

 5. Start autotest without any test argument, simply execute `python -m smoothtest.autotest.Command --smoothtest-settings settings.py`. It will open a browser, print some logging and give you an Ipython shell.
 
 6. We will specify the tested module from the shell, also we will make autotest to watch the `.html` file, so each time we change it, a test round is triggered.
 ```
 %autotest -t smoothtest/demos/xpath_browser_demo.py -F smoothtest/demos/html/xpath_browser_demo.html
 ```
 You will have an output similar the shown in point __1__. You mostly will care about the last line __[Master] 21:25:23: Received TestRunner's answer: EXCEPTIONS=0 FAILURES=0 ERRORS=0 from TOTAL=1__.
  
   a. Try modifying the html page and see how tests are triggered.

 7. In point __6__ we modified the current testing configuration via the `%autotest` magic command.

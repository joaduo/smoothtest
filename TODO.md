## Test failing and not reported

```
[Discover Runner] 06:31:21: Testing <function smoke_test_module at 0x7f4247728050> at smoothtest.webunittest.WebdriverManager
[Discover Runner] 06:31:21: Answering [AutotestAnswer(sent_cmd=AutotestCmd(cmd='_run_test', args=(<smoothtest.discover.TestDiscover.TestsContainer object at 0x7f42498724d0>,), kwargs={}), result=<SmoothTestResult run=1 errors=0 failures=1>, error=None)]
Process Process-20:
Traceback (most recent call last):
File "/usr/lib/python2.7/multiprocessing/process.py", line 258, in _bootstrap
self.run()
File "/usr/lib/python2.7/multiprocessing/process.py", line 114, in run
self._target(*self._args, **self._kwargs)
File "smoothtest/autotest/base.py", line 98, in __call__
self.callback(self.child_conn, *args, **kwargs)
File "smoothtest/discover/TestDiscover.py", line 178, in dispatch_cmds
self._dispatch_cmds(conn)
File "smoothtest/autotest/base.py", line 51, in _dispatch_cmds
send(answers)
File "smoothtest/autotest/base.py", line 33, in <lambda>
send = lambda msg: duplex and io_conn.send(msg)
PicklingError: Can't pickle <type 'thread.lock'>: attribute lookup thread.lock failed
Traceback (most recent call last):
File "smoothtest/discover/TestDiscover.py", line 158, in _prepare_and_run
answer = self.send_recv(self._run_test, tests)
File "smoothtest/autotest/base.py", line 173, in send_recv
return self._get_answer(self.recv(), cmd)
File "smoothtest/autotest/base.py", line 162, in recv
return self._subprocess_conn.recv()
EOFError
```

## High priority
1. install smoothtest(autotest) command X (smtest?)
1. Support screenshots comparison X
1. Keyboard interrupt kills webdriver. Why?
1. Perhaps we should kill the testrunner too?
1. Xpath: 
	Passing web browser
	NO:Using scrapy's hxs selector
	NO:Using scrapy's shell directly
	NO:Doing selections both, in scrapy and in webdriver
1. check /ticket/15403
   i. specify screenshot format function
   i. specify screenshot dir (by command line?)
1. fix current_path() to get all data
1. Rename WebdriverUtils to SmoothTestBrowser X
1. Extract xpath from WebdriverUtils.py into XpathWebdriver X
1. Extract also screenshots?
1. Identify child process
	i. return both to main at fork Main<-Master<-Slave
	i. keep track of them from main
		i. on every test? main->master? master->slave?
		if there is an IO error on PIPEs, then check pids (NOT READY)
	i. kill processes if still running when exiting. DONE!
1. Check Firefox and Xvfb processes
	i. get pid from Xvfb
	i. get pid from firefox/etc
	i. print warning if they keep running on exit
		i. kill if not kept
1. Multiplatform -> pickable fork callbacks (VERY HARD TO IMPLEMENT?)
1. Take screenshots

## TODO tests
1. test screenshots on test reports (w/wo)
1. test API with selenium

## TODO

1. check configglue and others for configuration
1. add support for .cfg configs
	1. passing config by command line?
1. Rename smoke to dry-run
1. add extensions
	i. has init/shutdown on the three levels (ui, main, test runner)
		i. an example extension would be webdriver (init and shutdown)
		i. virtualdisplay is another example
	i. adds ipython extensions
	i. enable extensions by configuration
1. replace stdout stderr for StringIO and read it from outside
1. split Interactive Main from non interactive Main (MainBase and Main)
1. create serious tests?
	have a project
		touch a file
	copy a file to a tested module
	tested with 
		except
		error
		failure
		ok -> writes result to file
	test smoke
	test browsers?
		open them and check UA?
1. phantomjs wait condition to be True does not work
1. passing arguments to a initialization module
	which will be ran on TestRunner (before or after forking (DO API))
	1. make testrunner with webdriver optional (pass testrunner module optionally ?)
		or perhaps optionally create your own command?
1. enable remote post-mortem debugging
1. better logging messages
	1. set log level per process
1. re-enable screenshots on exceptions (only on test methods)

1. make callbacks pickable in order to work with windows
1. browser pool
1. handle KeyboardInterrupt
1. Better test case module resolution
1. create smoothtest command
	i. autotest passing parameters or .cfg or .py
	i. create settings
1. Use ipdb to to step by step testing
	i. Use step back feature, s.step -1 
1. Detect CTRL+C and other...
1. Forward output messages to a specific process, so we can visualize in Eclipse
	(use openfd from a pipe?)
1. Restart closed webdriver?
1. Use specific profile for webdriver?
1. Detect "unable to connect" pages before selecting xpath?
2. Create better command line in ipython (selecting tests, exposing options, selecting browser, sending code)
4. Reset sessions, cache and cookies from running selenium instances
5. Having a pool of webdrivers
6. Having an eternal pool of webdrivers (in main process) to speed up testing
7. Play a sound on success/failure
	i. say "3" failed "4" Passed
	import pyttsx
	engine = pyttsx.init()
	engine.say('3 Failed, 4 Passed.')
	engine.runAndWait()
8. Enable remote messages (to enable shortcuts or commands via CLI)

## DONE

1. Add wipe_alerts method
1. Improve configuration framework
1. TestRunner addon -> Selenium Setup -> Virtual screen Setup
1. Rename parcial to partial
1. Create full_callback support and project watching support
1. Create autotest.py command `path/to/test.py [methods regex] -f [path to projects or files] [-F|-C|-P][--firefox|...]`

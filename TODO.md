## TODO


1. passing arguments to a initialization module
	which will be ran on TestRunner
	
	
1. handle KeyboardInterrupt
1. Better test case module resolution
1. create smoothtest command
	i. autotest passing parameters or .cfg or .py
	i. create settings
1. Rename parcial to partial
1. Use ipdb to to step by step testing
	i. Use step back feature, s.step -1 
1. Detect CTRL+C and other...
1. Forward output messages to a specific process, so we can visualize in Eclipse
	(use openfd from a pipe?)
1. Restart closed webdriver?
1. Use specific profile for webdriver?
1. Detect "unable to connect" pages before selecting xpath?
1. Create full_callback support and project watching support
1. Create autotest.py command `path/to/test.py [methods regex] -f [path to projects or files] [-F|-C|-P][--firefox|...]`
2. Create better command line in ipython (selecting tests, exposing options, selecting browser, sending code)
3. Improve configuration framework
4. Reset sessions, cache and cookies from running selenium instances
5. Having a pool of webdrivers
6. Having an eternal pool of webdrivers (in main process) to speed up testing
7. Play a sound on success/failure
	i. say "3" failed "4" Passed
	import pyttsx
	engine = pyttsx.init()
	engine.say('3 Failed, 4 Passed.')
	engine.runAndWait()
	
8. Enable remote messages (to enable shortcuts via CLI)


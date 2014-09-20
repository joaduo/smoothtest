smoothtest
==========

General purpose Testing Utilities and also special testing tools for for Web Applications


## TODO

0. Refactor
0. Create full_callback support and project watching support
1. Create autotest.py command `path/to/test.py [methods regex] -f [path to projects or files] [-F|-C|-P][--firefox|...]`
2. Create better command line in ipython (selecting tests, exposing options, selecting browser, sending code)
3. Improve configuration framework
4. Reset sessions, cache and cookies from running selenium instances
5. Having a pool of webdrivers
6. Having an eternal pool of webdrivers (in main process) to speed up testing
7. Play a sound on success/failure
	i. say "3" success "4" failed
8. Enable remote messages (to enable shortcuts via CLI)

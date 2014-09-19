# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
#from zmq.eventloop import ioloop
#ioloop.install = lambda:None

#from smoothtest.autotest.ioloop import install,AtPollZMQIOLoop
#install(AtPollZMQIOLoop)

from IPython.html.notebookapp import launch_new_instance, NotebookApp

#NotebookApp.kernel_manager.

from IPython.core import interactiveshell 

print interactiveshell.define_magic


#launch_new_instance()

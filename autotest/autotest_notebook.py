# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from IPython.external.path import path
from zmq.eventloop import ioloop
ioloop.install = lambda:None

from smoothtest.autotest.ioloop import install,AtPollZMQIOLoop
install(AtPollZMQIOLoop)

from IPython.html.notebookapp import launch_new_instance

launch_new_instance()

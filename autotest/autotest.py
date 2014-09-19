# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.AutotestContext import AutotestContext
from smoothtest.autotest.AutotestNotebook import AutotestNotebook

def child_callback(child_pipe):
    ctx = AutotestContext()
    
    def parcial_decorator(parcial_callback):
        def wrapper(*a, **kw):
            print 'Should run %s' % parcial_callback
            return parcial_callback(*a, **kw)
        return wrapper
    
    ctx.initialize(wait_type='select', parcial_decorator=parcial_decorator,
                   ipython_pipe=child_pipe)
    while 1:
        ctx.poll.next()

#TODO: disable CTRL+C signal on child!!
AutotestNotebook().init_notebook(child_callback)

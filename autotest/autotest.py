# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.AutotestContext import AutotestContext
from smoothtest.autotest.AutotestMain import AutotestMain

def child_callback(child_pipe):
    ctx = AutotestContext()
    
    def parcial_decorator(parcial_callback):
        def wrapper(*a, **kw):
            print 'Should run %s' % parcial_callback
            return parcial_callback(*a, **kw)
        return wrapper
    
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    parcial_reloads, full_reloads =['fulcrum/views/sales/tests/about_us.py'], []
    
    ctx.initialize(wait_type='select',
                   test_paths=test_paths,
                   parcial_reloads=parcial_reloads,
                   full_reloads=full_reloads,
                   parcial_decorator=parcial_decorator,
                   ipython_pipe=child_pipe)
    while 1:
        ctx.poll.next()

def run(embed_ipython=False):
    AutotestMain().run(child_callback, embed_ipython)

def main(argv=None):
    #TODO: disable CTRL+C signal on child!!
    run(embed_ipython=True)

if __name__ == "__main__":
    main()

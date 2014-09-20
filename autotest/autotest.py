# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.autotest.Context import Context
from smoothtest.autotest.Main import Main

def child_callback(child_pipe):
    ctx = Context()
    
    def parcial_decorator(parcial_callback):
        def wrapper(*a, **kw):
            print 'Should run %s' % parcial_callback
            #return parcial_callback(*a, **kw)
        return wrapper
    
    test_paths = ['fulcrum.views.sales.tests.about_us.AboutUs.test_contact_valid']
    parcial_reloads, full_reloads =['fulcrum/views/sales/tests/about_us.py'], []
    
    ctx.initialize(
                   test_paths=test_paths,
                   parcial_reloads=parcial_reloads,
                   full_reloads=full_reloads,
                   parcial_decorator=parcial_decorator,
                   child_conn=child_pipe)
    while 1:
        ctx.poll.next()

def run(embed_ipython=False):
    Main().run(child_callback, embed_ipython)

def main(argv=None):
    #TODO: disable CTRL+C signal on child!!
    run(embed_ipython=True)

if __name__ == "__main__":
    main()

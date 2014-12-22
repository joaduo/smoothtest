# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp
rel_imp.init()
from .Master import Master
from smoothtest.singleton_decorator import singleton_decorator


@singleton_decorator
class Context(object):

    def initialize(self, test_config, **kwargs):
        self.poll = Master().io_loop(test_config, **kwargs)

        def fake_initialize(*args, **kwargs):
            pass
        # Disable other initializations
        self.initialize = fake_initialize


def smoke_test_module():
    ctx = Context()
    ctx.initialize({}, block=False)
    for p in ctx.poll:
        pass

if __name__ == "__main__":
    smoke_test_module()

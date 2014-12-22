# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''


class singleton_decorator(object):

    '''
      Singleton pattern decorator.
      There will be only one instance of the decorated class.
      Decorator always returns same instance.
    '''

    def __init__(self, class_):
        self.class_ = class_
        self.instance = None

    def __call__(self, *a, **ad):
        if self.instance is None:
            self.instance = self.class_(*a, **ad)
        return self.instance


def smoke_test_module():
    @singleton_decorator
    class Foo(object):
        pass

    foo = Foo()
    assert foo is Foo()

if __name__ == "__main__":
    smoke_test_module()

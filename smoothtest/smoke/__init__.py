# -*- coding: utf-8 -*-
'''
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''


def fake_init(class_, instance=True):
    '''
    Fake initialization of a class to avoid calling it's real __init__
    method. (replacing with a dummy one that does nothing)
    BEWARE!!: this is only useful for testing methods independent from
    calling the real __init__
    :param class_: class_ to be instanced or __init__'s replaced
    :param instance: if False the new fake class is returned, if True
        an instance of the fake class is returned
    '''
    class fake_init(class_):

        def __init__(self):
            pass
    if instance:
        return fake_init()
    else:
        return fake_init

# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import pickle


def is_pickable(obj):
    try:
        pickle.dumps(obj)
        return True
    except:
        return False


def smoke_test_module():
    unpickable = lambda x: x
    assert not is_pickable(unpickable)
    assert is_pickable(1)

if __name__ == "__main__":
    smoke_test_module()

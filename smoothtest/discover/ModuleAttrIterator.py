# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
import rel_imp; rel_imp.init()
from types import ModuleType
from importlib import import_module
from ..base import SmoothTestBase
import pkgutil


class ModuleAttrIterator(SmoothTestBase):
    def iter_modules(self, package, filter_func, reload_=False):
        for module in self._gatherModules(package, reload_):
            yield module, list(self._filterModule(module, filter_func))

    def _filterModule(self, module, filter_func):
        for attr in module.__dict__.values():
            if (getattr(attr, '__module__', None) == module.__name__
            and filter_func(attr, module)):
                yield attr

    def _gatherModules(self, package, reload_):
        if (isinstance(package, ModuleType) 
        and not hasattr(package, '__path__')):
            yield package
        else:
            prefix = package.__name__ + '.'
            for _, modname, ispkg in pkgutil.walk_packages(package.__path__,
                                                           prefix):
                if not ispkg:
                    try:
                        module = import_module(modname)
                        if reload_:
                            module = reload(module)
                        yield module
                    except Exception as e:
                        self.log.e('Ignoring %s.%s. Exception: %r' % 
                                   (prefix,modname,e))
                    except SystemExit as e:
                        self.log.e('Ignoring %s.%s. SystemExit: %r' % 
                                   (prefix,modname,e)) 


def smoke_test_module():
    import smoothtest
    mai = ModuleAttrIterator()
    l = mai.log.d
    for i in mai.iter_modules(smoothtest, filter_func=lambda a,m: True):
        l(i)

if __name__ == "__main__":
    smoke_test_module()

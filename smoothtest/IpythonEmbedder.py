# -*- coding: utf-8 -*-
'''
Smoothtest
Copyright (c) 2014 Juju. Inc

Code Licensed under MIT License. See LICENSE file.
'''
from smoothtest.Logger import Logger

class IpythonEmbedder(object):
    def __init__(self, logger=None):
        self.log = logger or Logger(self.__class__.__name__)
        
    def embed(self, load_extension=None, kwargs=None):
        """Call this to embed IPython at the current point in your program.
        """
        iptyhon_msg = ('Could not embed Ipython, falling back to ipdb'
                       ' shell. Exception: %r')
        ipdb_msg = ('Could not embed ipdb, falling back to pdb'
                    ' shell. Exception: %r')
        try:
            self._embed_ipython(load_extension, kwargs)
        except Exception as e:
            self.log.w(iptyhon_msg % e)
            try:
                import ipdb
                ipdb.set_trace()
            except Exception as e:
                self.log.e(ipdb_msg % e)
                import pdb
                pdb.set_trace()

    def _embed_ipython(self, load_extension=None, kwargs=None):
        from IPython.terminal.ipapp import load_default_config
        from IPython.terminal.embed import InteractiveShellEmbed
        kwargs = kwargs or {}
        config = kwargs.get('config')
        header = kwargs.pop('header', u'')
        compile_flags = kwargs.pop('compile_flags', None)
        if config is None:
            config = load_default_config()
            config.InteractiveShellEmbed = config.TerminalInteractiveShell
            kwargs['config'] = config
        kwargs.setdefault('display_banner', False)
        self._ishell = InteractiveShellEmbed.instance(**kwargs)
        if load_extension:
            load_extension(self._ishell)
        # Stack depth is 3 because we use self.embed first
        self._ishell(header=header, stack_depth=3, compile_flags=compile_flags)
        return self._ishell


def smoke_test_module():
    IpythonEmbedder()

if __name__ == "__main__":
    smoke_test_module()

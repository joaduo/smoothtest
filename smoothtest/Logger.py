'''
Copyright (c) 2014, Juju Inc.
Copyright (c) 2011-2013, Joaquin G. Duo
'''
import logging


class Logger(object):
    default_level = logging.DEBUG
    handler_level = logging.DEBUG
    default_fmt = '%(asctime)s: %(message)s'
    default_datefmt = '%H:%M:%S'
    def __init__(self, name, output=None, level=None):
        if not level:
            level = self.default_level
        if not output:
            if not logging.root.handlers:
                output = self._config_output(name, level)
            else:
                output = logging.getLogger(name)
        self.output = output
        self.setLevel(level)

    def _config_output(self, name, level):
        hdlr = logging.StreamHandler()
        hdlr.setLevel(self.handler_level)
        logging.root.addHandler(hdlr)
        self.set_fmt()
        return logging.getLogger(name)
    
    def set_fmt(self, fmt=None, datefmt=None):
        datefmt = datefmt or self.default_datefmt
        fmt = fmt or self.default_fmt
        hdlr = logging.root.handlers[0]
        fmt = logging.Formatter(fmt=fmt,
                        datefmt=datefmt
                        )
        hdlr.setFormatter(fmt)
        
    def set_pre_post(self, pre='', post=''):
        self.set_fmt(fmt=pre+self.default_fmt+post)
        
    def critical(self, msg):
        self.output.critical(str(msg))
    def error(self, msg):
        self.output.error(str(msg))
    def warning(self, msg):
        self.output.warning(str(msg))
    def info(self, msg):
        self.output.info(str(msg))
    def debug(self, msg):
        self.output.debug(str(msg))
    def verbose(self, msg):
        self.output.debug(str(msg))
    def exception(self, msg):
        self.output.exception(str(msg))
    def c(self, msg):
        self.critical(msg)
    def e(self, msg):
        self.error(msg)
    def w(self, msg):
        self.warning(msg)
    def i(self, msg):
        self.info(msg)
    def d(self, msg):
        self.debug(msg)
    def v(self, msg):
        self.verbose(msg)
    def printFilePath(self, file_path, line=None, error=False):
        if error:
            out = self.e
        else:
            out = self.d
        if not line:
            line = 1
        msg = '  File "%s", line %d\n' % (file_path, line)
        out(msg)

    def setLevel(self, level):
        if hasattr(self.output, 'setLevel'):
            self.output.setLevel(level)
        else:
            self.w('Cannot set logging level')
    def __call__(self, msg):
        self.info(msg)


def smoke_test_module():
    ''' Simple self-contained test for the module '''
    logger = Logger('a.logger')
    logger.setLevel(logging.DEBUG)
    logger.set_pre_post(pre='Master ')
    #logger.set_fmt('')
    logger.critical('critical')
    logger.debug('debug')
    logger.error('error')
    logger.info('info')
    logger.warning('warning')
    logger('Call')

if __name__ == '__main__':
    smoke_test_module()

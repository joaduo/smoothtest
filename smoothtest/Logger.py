'''
Copyright (c) 2014, Juju Inc.
Copyright (c) 2011-2013, Joaquin G. Duo
'''
import logging

class Logger(object):
    default_level = logging.DEBUG
    handler_level = logging.DEBUG
    def __init__(self, name, output=None, level=None):
        if not level:
            level = self.default_level
        if not output:
            if not len(logging.root.handlers):
                output = self.__configLogging(name, level)
            else:
                output = logging.getLogger(name)
        self.output = output
        self.setLevel(level)

    def __configLogging(self, name, level):
        hdlr = logging.StreamHandler()
        hdlr.setLevel(self.handler_level)
        fmt = logging.Formatter(fmt='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
        hdlr.setFormatter(fmt)
        logging.root.addHandler(hdlr)
        return logging.getLogger(name)

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

def smokeTestModule():
    ''' Simple self-contained test for the module '''
    logger = Logger('a.logger')
    logger.setLevel(logging.DEBUG)
#  logger.critical('critical')
    logger.debug('debug')
#  logger.error('error')
    logger.info('info')
    logger.warning('warning')
    logger('Call')

if __name__ == '__main__':
    smokeTestModule()

"""

"""
import unittest
from smoothtest.HTMLTestRunner import HTMLTestRunner


class HTMLTestRunnerNew(HTMLTestRunner):
    #TODO:
    #specify output.html
    #specify template html file
    #pass smoothtest settings
    pass


class TestProgram(unittest.TestProgram):

    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
#    def __init__(self, module='__main__', defaultTest=None, argv=None,
#                    testRunner=None, testLoader=loader.defaultTestLoader,
#                    exit=True, verbosity=1, failfast=None, catchbreak=None,
#                    buffer=None):
#        #...
#        self.parseArgs(argv)
#        self.runTests()
#    def parseArgs(self, argv):
#        pass
#    def usageExit(self, msg=None):

    def runTests(self):
        # Pick HTMLTestRunner as the default test runner.
        # base class's testRunner parameter is not useful because it means
        # we have to instantiate HTMLTestRunner before we know self.verbosity.
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)


def TestRunnerCommand(object):
    def get_parser(self):
        pass
    
    def build_test_program(self, argv=None):
        pass
        TestProgram(module=None)


def main(argv=None):
    pass

##############################################################################
# Executing this module from the command line
##############################################################################


def smoke_test_module():
    # Disable warning for missing test
    pass

if __name__ == "__main__":
    main()

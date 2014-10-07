
import rel_imp; rel_imp.init()
import sys
#We want to use the new version of unittest in <= python 2.6
if sys.version_info < (2,7):
    import unittest2 as unittest
else:
    import unittest
from .TestCase import TestCase

main = unittest.main
TestCase = TestCase
unittest = unittest

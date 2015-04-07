'''
'''
import unittest
from smoothtest.webunittest.WebdriverUtils import Url

class TestWebdriverUtilsUrl(unittest.TestCase):
    def test_urls(self):
        u = u'https://www.google.cl/?gfe_rd=cr&ei=ix0kVfH8M9PgwASPoIFo&gws_rd=ssl'
        self.assertAlmostEqual(Url(u).get_path_and_on(), '/?gfe_rd=cr&ei=ix0kVfH8M9PgwASPoIFo&gws_rd=ssl')

if __name__ == "__main__":
    unittest.main()

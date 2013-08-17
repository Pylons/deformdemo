import unittest
from pyramid.paster import bootstrap
from deformdemo import DeformDemo


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        bs = bootstrap('demo.ini')
        app = bs['app']
        self.request = bs['request']
        from webtest import TestApp
        self.testapp = TestApp(app)
        self.demos = DeformDemo(self.request)

    def test_valid_html(self):
        demos_urls = self.demos.get_demos()
        for demo in demos_urls:
            res = self.testapp.get(demo[1], status=200)
            import pdb; pdb.set_trace()  # NOQA
        #self.failUnless('Pyramid' in res.body)

if __name__ == '__main__':
    unittest.main()

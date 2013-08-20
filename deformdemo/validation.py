from pyramid.paster import bootstrap
from deformdemo import DeformDemo
import unittest
import httplib
import sys
import re
import urlparse
import gzip
import StringIO
import json


def validate(data):

    extPat = re.compile(r'^.*\.([A-Za-z]+)$')
    extDict = {
        "html": "text/html",
        "htm": "text/html",
        "xhtml": "application/xhtml+xml",
        "xht": "application/xhtml+xml",
        "xml": "application/xml",
    }


    errorsOnly = 0
    encoding = None
    contentType = "text/html"
    service = 'http://html5.validator.nu/'

    buf = StringIO.StringIO()
    gzipper = gzip.GzipFile(fileobj=buf, mode='wb')
    gzipper.write(data)
    gzipper.close()
    gzippeddata = buf.getvalue()
    buf.close()

    connection = None
    response = None
    status = 302
    redirectCount = 0

    url = service + '?out=json'
    url = service + '?out=text'
    if errorsOnly:
        url = url + '&level=error'

    while (status == 302 or status == 301 or status == 307) and redirectCount < 10:
        if redirectCount > 0:
            url = response.getheader('Location')
        parsed = urlparse.urlsplit(url)
        if parsed[0] != 'http':
            sys.stderr.write('URI scheme %s not supported.\n' % parsed[0])
            sys.exit(7)
        if redirectCount > 0:
            connection.close() # previous connection
            print 'Redirecting to %s' % url
            print 'Please press enter to continue or type "stop" followed by enter to stop.'
            if raw_input() != "":
                sys.exit(0)
        connection = httplib.HTTPConnection(parsed[1])
        connection.connect()
        connection.putrequest("POST", "%s?%s" % (parsed[2], parsed[3]), skip_accept_encoding=1)
        connection.putheader("Accept-Encoding", 'gzip')
        connection.putheader("Content-Type", contentType)
        connection.putheader("Content-Encoding", 'gzip')
        connection.putheader("Content-Length", len(gzippeddata))
        connection.endheaders()
        connection.send(gzippeddata)
        response = connection.getresponse()
        status = response.status
        redirectCount += 1

    if status != 200:
        sys.stderr.write('%s %s\n' % (status, response.reason))
        sys.exit(5)

    if response.getheader('Content-Encoding', 'identity').lower() == 'gzip':
        response = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))

    connection.close()
    return response.read()
    result = json.loads(response.read())
    return result



class FunctionalTests(unittest.TestCase):
    def setUp(self):
        bs = bootstrap('demo.ini')
        app = bs['app']
        self.request = bs['request']
        from webtest import TestApp
        self.testapp = TestApp(app)
        self.demos = DeformDemo(self.request)

    def test_valid_html(self):
        errors = []
        demos_urls = self.demos.get_demos()
        for demo in demos_urls:
            res = self.testapp.get(demo[1], status=200)
            check = validate(res.body)
            #import pdb; pdb.set_trace()  # NOQA
            try:
                self.assertFalse(check)
                print demo[0], "."
            except AssertionError, e:
                errors.append((demo[0], check))
                print demo[0], "E"
                print check
                print
        #self.assertFalse(errors)

if __name__ == '__main__':
    unittest.main()

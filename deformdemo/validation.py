import gzip
import sys
import unittest

from pyramid.paster import bootstrap

from io import BytesIO
import http.client
import urllib.parse

# Deform Demo
from deformdemo import DeformDemo

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, " \
        "like Gecko) Chrome/119.0.0.0 Safari/537.36"


def validate(data):
    errorsOnly = 0
    contentType = "text/html"
    service = "http://html5.validator.nu/"

    buf = BytesIO()
    gzipper = gzip.GzipFile(fileobj=buf, mode="wb")
    gzipper.write(data)
    gzipper.close()
    gzippeddata = buf.getvalue()
    buf.close()

    connection = None
    response = None
    status = 302
    redirectCount = 0

    url = service + "?out=json"
    url = service + "?out=text"
    if errorsOnly:
        url = url + "&level=error"

    while (
        status == 302 or status == 301 or status == 307
    ) and redirectCount < 10:
        if redirectCount > 0:
            url = response.getheader("Location")
        parsed = urllib.parse.urlsplit(url)
        if parsed[0] != "http":
            sys.stderr.write(
                "URI scheme {0} not supported.\n".format(parsed[0])
            )
            sys.exit(7)
        if redirectCount > 0:
            connection.close()  # previous connection
            print("Redirecting to {0}".format(url))
            print(
                "Please press enter to continue or type 'stop' "
                "followed by enter to stop."
            )
            if input() != "":
                sys.exit(0)
        connection = http.client.HTTPConnection(parsed[1])
        connection.connect()
        connection.putrequest(
            "POST",
            "{0}?{1}".format(parsed[2], parsed[3]),
            skip_accept_encoding=1,
        )
        connection.putheader("Accept-Encoding", "gzip")
        connection.putheader("Content-Type", contentType)
        connection.putheader("Content-Encoding", "gzip")
        connection.putheader("Content-Length", len(gzippeddata))
        connection.putheader("User-Agent", UA)
        connection.endheaders()
        connection.send(gzippeddata)
        response = connection.getresponse()
        status = response.status
        redirectCount += 1

    if status != 200:
        sys.stderr.write("%s %s\n" % (status, response.reason))
        sys.exit(5)

    if response.getheader("Content-Encoding", "identity").lower() == "gzip":
        response = gzip.GzipFile(fileobj=BytesIO(response.read()))

    connection.close()
    return response.read()


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        bs = bootstrap("demo.ini")
        app = bs["app"]
        self.request = bs["request"]
        from webtest import TestApp

        self.testapp = TestApp(app)
        self.demos = DeformDemo(self.request)

    def test_valid_html(self):
        errors = []
        demos_urls = self.demos.get_demos()
        for demo in demos_urls:
            res = self.testapp.get(demo[1], status=200)
            check = validate(res.body)
            # import pdb; pdb.set_trace()  # NOQA
            try:
                self.assertFalse(check)
                print(demo[0], ".")
            except AssertionError:
                errors.append((demo[0], check))
                print(demo[0], "E")
                print(check.decode())
                print("")
        # self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()

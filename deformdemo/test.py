# -*- coding: utf-8 -*-

import unittest
import re
import os

# to run:
# console 1: java -jar selenium-server.jar
# console 2: start the deform demo server (pserve demo.ini)
# console 3: python2.X test.py

# Note that this test file does not run under Python 3, but it can be used
# to test a deformdemo *instance* running under Python 3.

# Instead of using -browserSessionReuse as an arg to
# selenium-server.jar to speed up tests, we rely on
# setUpModule/tearDownModule functionality.

browser = None

BASE_PATH = os.environ.get('BASE_PATH', '')
URL = os.environ.get('URL', 'http://localhost:8521')

def setUpModule():
    from selenium.webdriver import Firefox
    global browser
    browser = Firefox()
    return browser

def tearDownModule():
    browser.close()

def _getFile(name='test.py'):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    filename = os.path.split(path)[-1]
    return path, filename

# appease nosetests by giving a default argument, it thinks this is a test
def test_url(url=''): 
    return URL + BASE_PATH + url

class Base(object):
    urepl = re.compile('\\bu(\'.*?\'|".*?")')
    setrepl = re.compile('set\(\[(.*)\]\)')

    def setUp(self):
        browser.get(self.url)

    def assertSimilarRepr(self, a, b):
        # ignore u'' and and \n in reprs, normalize set syntax between py2 and
        # py3
        ar = a.replace('\n', '')
        ar = self.urepl.sub(r'\1', ar)
        ar = self.setrepl.sub(r'{\1}', ar)
        br = b.replace('\n', '')
        br = self.urepl.sub(r'\1', br)
        br = self.setrepl.sub(r'{\1}', br)
        self.assertEqual(ar.replace(' ', ''), br.replace(' ', ''))

class CheckboxChoiceWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkboxchoice/")
    def test_render_default(self):
        self.assertTrue('Pepper' in browser.page_source)
        self.assertFalse(browser.find_element_by_id('deformField1-0').is_selected())
        self.assertFalse(browser.find_element_by_id('deformField1-1').is_selected())
        self.assertFalse(browser.find_element_by_id('deformField1-2').is_selected())
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Pepper')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_unchecked(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        error_node = 'error-deformField1'
        self.assertEqual(browser.find_element_by_id(error_node).text,
                         'Shorter than minimum length 1')
        self.assertFalse(browser.find_element_by_id('deformField1-0').is_selected())
        self.assertFalse(browser.find_element_by_id('deformField1-1').is_selected())
        self.assertFalse(browser.find_element_by_id('deformField1-2').is_selected())
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_one_checked(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id("deformField1-0").click()
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertTrue(browser.find_element_by_id('deformField1-0').is_selected())
        captured = browser.find_element_by_id('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'habanero'}}",
            )

    def test_submit_three_checked(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id("deformField1-0").click()
        browser.find_element_by_id("deformField1-1").click()
        browser.find_element_by_id("deformField1-2").click()
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertTrue(browser.find_element_by_id('deformField1-0').is_selected())
        self.assertTrue(browser.find_element_by_id('deformField1-1').is_selected())
        self.assertTrue(browser.find_element_by_id('deformField1-2').is_selected())
        captured = browser.find_element_by_id('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'chipotle', 'habanero', 'jalapeno'}}",
            )

class CheckboxWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkbox/")
    def test_render_default(self):
        self.assertTrue('I Want It!' in browser.page_source)
        self.assertFalse(browser.find_element_by_id('deformField1').is_selected())
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'I Want It!')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_unchecked(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertFalse(browser.find_element_by_id('deformField1').is_selected())
        self.assertEqual(browser.find_element_by_id('captured').text, "{'want': False}")

    def test_submit_checked(self):
        browser.find_element_by_id("deformField1").click()
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_id('deformField1').is_selected())
        self.assertEqual(browser.find_element_by_id('captured').text, "{'want': True}")
    
class CheckedInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedinput/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertTrue('Email Address' in browser.page_source)
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Email Address')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_invalid(self):
        browser.find_element_by_id('deformField1').send_keys('this')
        browser.find_element_by_id('deformField1-confirm').send_keys('this')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Invalid email address')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'this')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'this')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_mismatch(self):
        browser.find_element_by_id('deformField1').send_keys('this@example.com')
        browser.find_element_by_id('deformField1-confirm').send_keys('that@example.com')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Fields did not match')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'this@example.com')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'that@example.com')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('user@example.com')
        browser.find_element_by_id('deformField1-confirm').send_keys('user@example.com')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'user@example.com')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'user@example.com')
        self.assertEqual(browser.find_element_by_id('captured').text, "{'email': u'user@example.com'}")

class CheckedInputWidgetWithMaskTests(Base, unittest.TestCase):
    url = test_url("/checkedinput_withmask/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Social Security Number')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '###-##-####')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')

    def test_type_bad_input(self):
        browser.find_element_by_id('deformField1').send_keys('a')
        browser.find_element_by_id('deformField1-confirm').send_keys('a')
        self.assertTrue(browser.find_element_by_id('deformField1').get_attribute('value') in ('', '###-##-####'))
        self.assertTrue(browser.find_element_by_id('deformField1-confirm').get_attribute('value') in ('', '###-##-####'))

    def test_submit_success(self):
        browser.find_element_by_id('deformField1').send_keys('140118866')
        browser.execute_script('document.getElementById("deformField1-confirm").focus();')
        browser.find_element_by_id('deformField1-confirm').send_keys('140118866')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('captured').text, "{'ssn': u'140-11-8866'}")

class CheckedPasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Password')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('type'), 'password')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('type'), 'password')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_tooshort(self):
        browser.find_element_by_id('deformField1').send_keys('this')
        browser.find_element_by_id('deformField1-confirm').send_keys('this')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Shorter than minimum length 5')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'this')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'this')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_mismatch(self):
        browser.find_element_by_id('deformField1').send_keys('this123')
        browser.find_element_by_id('deformField1-confirm').send_keys('that123')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Password did not match confirm')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'this123')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'that123')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('this123')
        browser.find_element_by_id('deformField1-confirm').send_keys('this123')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'this123')
        self.assertEqual(browser.find_element_by_id('deformField1-confirm').get_attribute('value'), 'this123')
        self.assertEqual(browser.find_element_by_id('captured').text, "{'password': u'this123'}")

class DateInputWidgetTests(Base, unittest.TestCase):
    url = test_url('/dateinput/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Date"))
        self.assertEqual(browser.get_text('css=.required'), 'Date')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertEqual(browser.get_value('deformField1'), '2010-05-05')
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_empty(self):
        browser.get(self.url)
        browser.type('deformField1', '')
        browser.click("submit")
        self.assertTrue(browser.get_text('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node), 'Required')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_tooearly(self):
        browser.get(self.url)
        browser.focus('css=#deformField1')
        browser.click('css=#deformField1')
        browser.click('link=4')
        browser.click("submit")
        self.assertTrue(browser.get_text('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node),
                         '2010-05-04 is earlier than earliest date 2010-05-05')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_success(self):
        browser.get(self.url)
        browser.focus('css=#deformField1')
        browser.click('css=#deformField1')
        browser.click('link=6')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#captured'),
                         "{'date': datetime.date(2010, 5, 6)}")
        self.assertEqual(browser.get_value('deformField1'), '2010-05-06')

class DateTimeInputWidgetTests(Base, unittest.TestCase):
    url = test_url('/datetimeinput/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Date Time"))
        self.assertEqual(browser.get_text('css=.required'), 'Date Time')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertEqual(browser.get_value('deformField1'), '2010-05-06 12:00:00')
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_empty(self):
        browser.get(self.url)
        browser.type('deformField1', '')
        browser.click("submit")
        self.assertTrue(browser.get_text('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node), 'Required')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_tooearly(self):
        browser.get(self.url)
        browser.focus('css=#deformField1')
        browser.click('css=#deformField1')
        browser.click('link=5')
        browser.click("submit")
        self.assertTrue(browser.get_text('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node),
                         '2010-05-05 12:00:00+00:00 is earlier than earliest datetime 2010-05-05 12:30:00+00:00')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_success(self):
        browser.get(self.url)
        browser.focus('css=#deformField1')
        browser.click('css=#deformField1')
        browser.click('link=7')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertTrue(browser.get_text('css=#captured').startswith(
            "{'date_time': datetime.datetime(2010, 5, 7, 12, 0, tzinfo"))
        self.assertEqual(browser.get_value('deformField1'), '2010-05-07 12:00:00')

class DatePartsWidgetTests(Base, unittest.TestCase):
    url = test_url('/dateparts/')
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertTrue('Date' in browser.page_source)
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Date')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '')
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))

    def test_submit_only_year(self):
        browser.find_element_by_id('deformField1').send_keys('2010')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Incomplete date')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '')
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))

    def test_submit_only_year_and_month(self):
        browser.find_element_by_id('deformField1').send_keys('2010')
        browser.find_element_by_id('deformField1-month').send_keys('1')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Incomplete date')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '1')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '')

    def test_submit_tooearly(self):
        browser.find_element_by_id('deformField1').send_keys('2008')
        browser.find_element_by_id('deformField1-month').send_keys('1')
        browser.find_element_by_id('deformField1-day').send_keys('1')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text,
                         '2008-01-01 is earlier than earliest date 2010-01-01')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '2008')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '1')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '1')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('2010')
        browser.find_element_by_id('deformField1-month').send_keys('1')
        browser.find_element_by_id('deformField1-day').send_keys('1')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('captured').text,
                         "{'date': datetime.date(2010, 1, 1)}")
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField1-month').get_attribute('value'), '01')
        self.assertEqual(browser.find_element_by_id('deformField1-day').get_attribute('value'), '01')

class EditFormTests(Base, unittest.TestCase):
    url = test_url("/edit/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '42')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('name'), 'number')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('name'), 'name')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('name'), 'year')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('value'), '04')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('name'), 'month')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('value'), '09')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('name'), 'day')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField3').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField3').send_keys('name')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '42')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), 'name')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('value'), '04')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('value'), '09')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            (u"{'mapping': {'date': datetime.date(2010, 4, 9), "
             "'name': u'name'}, 'number': 42}"))

class MappingWidgetTests(Base, unittest.TestCase):
    url = test_url("/mapping/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('value'), '')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('error-deformField3').text, 'Required')
        self.assertEqual(browser.find_element_by_id('error-deformField4').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_invalid_number(self):
        browser.find_element_by_id('deformField1').send_keys('notanumber')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, '"notanumber" is not a number')
        self.assertEqual(browser.find_element_by_id('error-deformField3').text, 'Required')
        self.assertEqual(browser.find_element_by_id('error-deformField4').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_invalid_date(self):
        browser.find_element_by_id('deformField1').send_keys('1')
        browser.find_element_by_id('deformField3').send_keys('name')
        browser.find_element_by_id('deformField4').send_keys('year')
        browser.find_element_by_id('deformField4-month').send_keys('month')
        browser.find_element_by_id('deformField4-day').send_keys('day')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField4').text, 'Invalid date')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '1')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), 'name')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('value'), 'year')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('value'), 'month')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('value'), 'day')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success(self):
        browser.find_element_by_id('deformField1').send_keys('1')
        browser.find_element_by_id('deformField3').send_keys('name')
        browser.find_element_by_id('deformField4').send_keys('2010')
        browser.find_element_by_id('deformField4-month').send_keys('1')
        browser.find_element_by_id('deformField4-day').send_keys('1')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '1')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), 'name')
        self.assertEqual(browser.find_element_by_id('deformField4').get_attribute('value'), '2010')
        self.assertEqual(browser.find_element_by_id('deformField4-month').get_attribute('value'), '01')
        self.assertEqual(browser.find_element_by_id('deformField4-day').get_attribute('value'), '01')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            (u"{'mapping': {'date': datetime.date(2010, 1, 1), "
             "'name': u'name'}, 'number': 1}"))

class FieldDefaultTests(Base, unittest.TestCase):
    url = test_url("/fielddefaults/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'Grandaddy')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'Just Like the Fambly Cat')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'Grandaddy')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'Just Like the Fambly Cat')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('error-deformField3').text, 'Required')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').clear()
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id('deformField2').clear()
        browser.find_element_by_id('deformField2').send_keys('def')
        browser.find_element_by_id('deformField3').clear()
        browser.find_element_by_id('deformField3').send_keys('ghi')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'def')
        self.assertEqual(browser.find_element_by_id('deformField3').get_attribute('value'), 'ghi')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            u"{'album': u'def', 'artist': u'abc', 'song': u'ghi'}")

class NonRequiredFieldTests(Base, unittest.TestCase):
    url = test_url("/nonrequiredfields/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success_required_filled_notrequired_empty(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            u"{'notrequired': u'', 'required': u'abc'}")

    def test_submit_success_required_and_notrequired_filled(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id('deformField2').send_keys('def')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'def')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            u"{'notrequired': u'def', 'required': u'abc'}")

class HiddenFieldWidgetTests(Base, unittest.TestCase):
    url = test_url("/hidden_field/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'true')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_render_submitted(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'true')
        self.assertEqual(browser.find_element_by_id('captured').text, "{'sneaky': True}")

class HiddenmissingTests(Base, unittest.TestCase):
    url = test_url("/hiddenmissing/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_render_submitted(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('yup')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'yup')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            "{'number': <colander.null>, 'title': u'yup'}")

class FileUploadTests(Base, unittest.TestCase):
    url = test_url("/file/")

    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_filled(self):
        from selenium.common.exceptions import NoSuchElementException

        # submit one first
        path, filename = _getFile()
        browser.find_element_by_id('deformField1').send_keys(path)
        browser.find_element_by_id("deformsubmit").click()

        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField1-filename').text, filename)
        self.assertTrue(filename in browser.find_element_by_id('captured').text)
        uid = browser.find_element_by_id('deformField1-uid').get_attribute('value')
        self.assertTrue(uid in browser.find_element_by_id('captured').text)

        # resubmit without entering a new filename should not change the file
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('deformField1-filename').text, filename)
        self.assertEqual(browser.find_element_by_id('deformField1-uid').get_attribute('value'), uid)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile('selenium.py')
        browser.find_element_by_id('deformField1').send_keys(path2)
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_id('deformField1-filename').text, filename2)
        self.assertTrue('filename' in browser.find_element_by_id('captured').text)
        self.assertTrue(uid in browser.find_element_by_id('captured').text)

class InterFieldValidationTests(Base, unittest.TestCase):
    url=  test_url("/interfield/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_both_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_id('error-deformField2').text, 'Required')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_one_empty(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertRaises(NoSuchElementException, browser.find_element_by_id, 'error-deformField1')
        self.assertEqual(browser.find_element_by_id('error-deformField2').text, 'Required')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_first_doesnt_start_with_second(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id('deformField2').send_keys('def')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue(browser.find_element_by_css_selector('.has-error'))
        self.assertRaises(NoSuchElementException, browser.find_element_by_id, 'error-deformField1')
        self.assertEqual(browser.find_element_by_id('error-deformField2').text, 'Must start with name abc')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'def')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')

    def test_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abc')
        browser.find_element_by_id('deformField2').send_keys('abcdef')
        browser.find_element_by_id("deformsubmit").click()
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertRaises(NoSuchElementException, browser.find_element_by_id, 'error-deformField1')
        self.assertRaises(NoSuchElementException, browser.find_element_by_id, 'error-deformField1')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(browser.find_element_by_id('deformField2').get_attribute('value'), 'abcdef')
        self.assertEqual(eval(browser.find_element_by_id('captured').text),
                         {'name': 'abc', 'title': 'abcdef'})

class InternationalizationTests(Base, unittest.TestCase):
    url = test_url("/i18n/")

    def setUp(self):
        pass  # each tests has a different url

    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.get(self.url)
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_css_selector('label').text, 'A number between 1 and 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, 'Submit')

    def test_render_en(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.get("%s?_LOCALE_=en" % self.url)
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_css_selector('label').text, 'A number between 1 and 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, 'Submit')
    
    def test_render_ru(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.get("%s?_LOCALE_=ru" % self.url)
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_css_selector('label').text, u'Число между 1 и 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, u'отправить')
    
    def test_submit_empty_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_css_selector('.alert-danger').text, 'There was a problem with your submission')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')
        self.assertEqual(browser.find_element_by_css_selector('label').text, 'A number between 1 and 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, 'Submit')

    def test_submit_empty_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_css_selector('.alert-danger').text, u'Данные которые вы предоставили содержат ошибку')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, u'Требуется')
        self.assertEqual(browser.find_element_by_css_selector('label').text, u'Число между 1 и 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, u'отправить')

    def test_submit_toolow_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        browser.find_element_by_id('deformField1').send_keys('0')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_css_selector('.alert-danger').text, 'There was a problem with your submission')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, '0 is less than minimum value 1')
        self.assertEqual(browser.find_element_by_css_selector('label').text, 'A number between 1 and 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, 'Submit')

    def test_submit_toolow_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        browser.find_element_by_id('deformField1').send_keys('0')
        browser.find_element_by_id("deformsubmit").click()
        self.assertEqual(browser.find_element_by_css_selector('.alert-danger').text, u'Данные которые вы предоставили содержат ошибку')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, u'0 меньше чем 1')
        self.assertEqual(browser.find_element_by_css_selector('label').text, u'Число между 1 и 10')
        self.assertEqual(browser.find_element_by_id("deformsubmit").text, u'отправить')


class PasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/password/")
    def test_render_default(self):
        from selenium.common.exceptions import NoSuchElementException
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Password')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')

    def test_render_submit_empty(self):
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(browser.find_element_by_css_selector('.required').text, 'Password')
        self.assertEqual(browser.find_element_by_id('captured').text, 'None')
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), '')
        self.assertEqual(browser.find_element_by_id('error-deformField1').text, 'Required')

    def test_render_submit_success(self):
        from selenium.common.exceptions import NoSuchElementException
        browser.find_element_by_id('deformField1').send_keys('abcdef123')
        browser.find_element_by_id("deformsubmit").click()
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(browser.find_element_by_id('deformField1').get_attribute('value'), 'abcdef123')
        self.assertRaises(NoSuchElementException, browser.find_element_by_css_selector, '.has-error')
        self.assertSimilarRepr(
            browser.find_element_by_id('captured').text,
            "{'password': u'abcdef123'}")

class RadioChoiceWidgetTests(Base, unittest.TestCase):
    url = test_url("/radiochoice/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Pepper"))
        self.assertFalse(browser.is_checked("deformField1-0"))
        self.assertFalse(browser.is_checked("deformField1-1"))
        self.assertFalse(browser.is_checked("deformField1-2"))
        self.assertEqual(browser.get_text('css=.required'), 'Pepper')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_unchecked(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertTrue(browser.get_text('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node), 'Required')
        self.assertFalse(browser.is_checked("deformField1-0"))
        self.assertFalse(browser.is_checked("deformField1-1"))
        self.assertFalse(browser.is_checked("deformField1-2"))
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_one_checked(self):
        browser.get(self.url)
        browser.click("deformField1-0")
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertTrue(browser.is_checked("deformField1-0"))
        self.assertSimilarRepr(
            browser.get_text('css=#captured'),
            "{'pepper': u'habanero'}")

class RadioChoiceWidgetIntTests(RadioChoiceWidgetTests):
    url = test_url("/radiochoice_int/")
    def test_submit_one_checked(self):
        browser.get(self.url)
        browser.click("deformField1-0")
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertTrue(browser.is_checked("deformField1-0"))
        self.assertSimilarRepr(
            browser.get_text('css=#captured'),
            "{'pepper': 0}")

class ReadOnlySequenceOfMappingTests(Base, unittest.TestCase):
    url = test_url("/readonly_sequence_of_mappings/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField6'), 'name1')
        self.assertEqual(browser.get_text('deformField7'), '23')
        self.assertEqual(browser.get_text('deformField9'), 'name2')
        self.assertEqual(browser.get_text('deformField10'), '25')

class SequenceOfRadioChoices(Base, unittest.TestCase):
    url = test_url("/sequence_of_radiochoices/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Pepper Chooser')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Pepper Chooser')
        self.assertEqual(browser.get_text('css=#captured'), "{'peppers': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_filled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click('dom=document.forms[0].elements[5]')
        browser.click('dom=document.forms[0].elements[11]')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertEqual(eval(captured),
                         {'peppers': ['habanero', 'jalapeno']})

class SequenceOfDefaultedSelects(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Pepper Chooser')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Pepper Chooser')
        self.assertEqual(browser.get_text('css=#captured'), "{'peppers': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_filled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertEqual(eval(captured), # should be 2 values, both defaults
                         {'peppers': ['jalapeno', 'jalapeno']})

class SequenceOfDefaultedSelectsWithInitialItem(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects_with_initial_item/")
    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Pepper Chooser')
        captured = browser.get_text('css=#captured')
        self.assertEqual(eval(captured), # should be 1 value (min_len 1)
                         {'peppers': ['jalapeno']})
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_one_added(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertEqual(eval(captured), # should be 2 values, both defaults
                         {'peppers': ['jalapeno', 'jalapeno']})

class SequenceOfFileUploads(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'), 'Add Upload')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'), 'Add Upload')
        self.assertEqual(browser.get_text('css=#captured'), "{'uploads': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_upload_one_success(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        path, filename = _getFile()
        browser.type("dom=document.forms[0].upload", path)
        browser.click("submit")

        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_attribute('deformField3@name'), 'upload')
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename)
        uid = browser.get_value('css=#deformField3-uid')
        captured = browser.get_text('css=#captured')
        self.assertTrue("'filename': u'%s" % filename in captured)
        self.assertTrue(uid in captured)
    
    def test_upload_multi_interaction(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        path, filename = _getFile()
        browser.type("dom=document.forms[0].upload", path)
        browser.click("submit")

        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_attribute('deformField3@name'), 'upload')
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename)
        uid = browser.get_value('css=#deformField3-uid')
        captured = browser.get_text('css=#captured')
        self.assertTrue("'filename': u'%s" % filename in captured)
        self.assertTrue(uid in captured)
    
        # resubmit without entering a new filename should not change the file
        browser.click('submit')
        self.assertEqual(browser.get_value('css=#deformField3-uid'), uid)
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile('selenium.py')
        browser.type('deformField3', path2)
        browser.click('submit')
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename2)
        captured = browser.get_text('css=#captured')
        self.assertTrue("'filename': u'%s" % filename2 in captured)
        self.assertEqual(browser.get_value('css=#deformField3-uid'), uid)

        # add a new file
        browser.click('deformField1-seqAdd')
        path, filename = _getFile()
        browser.type("dom=document.forms[0].upload[1]", path)
        browser.click("submit")
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename2)
        self.assertEqual(browser.get_text('css=#deformField4-filename'),
                         filename)
        captured = browser.get_text('css=#captured')
        uid2 = browser.get_value('css=#deformField4-uid')
        self.assertTrue("'filename': u'%s" % filename2 in captured)
        self.assertTrue("'filename': u'%s" % filename in captured)
        self.assertEqual(browser.get_value('css=#deformField3-uid'), uid)
        
        # resubmit should not change either file
        browser.click('submit')
        self.assertEqual(browser.get_value('css=#deformField3-uid'), uid)
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename2)
        self.assertEqual(browser.get_value('css=#deformField4-uid'), uid2)
        self.assertEqual(browser.get_text('css=#deformField4-filename'),
                         filename)

        # remove a file
        browser.click('deformField4-close')
        browser.click('submit')
        self.assertEqual(browser.get_value('css=#deformField3-uid'), uid)
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename2)
        self.assertFalse(browser.is_element_present('css=#deformField4-uid'))
        captured = browser.get_text('css=#captured')
        self.assertFalse("'filename': u'%s" % filename in captured)

class SequenceOfFileUploadsWithInitialItem(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads_with_initial_item/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'), 'Add Upload')
        self.assertEqual(browser.get_attribute('deformField3@name'),
                         'upload')
        self.assertEqual(browser.get_attribute('deformField3@type'),
                         'file')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_upload_one_success(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        path, filename = _getFile()
        browser.type("dom=document.forms[0].upload[0]", path)
        browser.type("dom=document.forms[0].upload[1]", path)
        browser.click("submit")

        self.assertFalse(browser.is_element_present('css=.has-error'))

        # first element present
        self.assertEqual(browser.get_attribute('deformField3@name'), 'upload')
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertEqual(browser.get_text('css=#deformField3-filename'),
                         filename)
        uid = browser.get_value('css=#deformField3-uid')

        # second element present
        self.assertEqual(browser.get_attribute('deformField4@name'), 'upload')
        self.assertEqual(browser.get_value('deformField4'), '')
        self.assertEqual(browser.get_text('css=#deformField4-filename'),
                         filename)
        uid = browser.get_value('css=#deformField3-uid')

        # got some files
        captured = browser.get_text('css=#captured')
        self.assertTrue("'filename': u'%s" % filename in captured)
        self.assertTrue(uid in captured)

class SequenceOfMappings(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_element_present('css=.deformProto'))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Person')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Person')
        self.assertEqual(browser.get_text('css=#captured'), "{'people': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField6'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField7'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField9'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField10'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_complex_interaction(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd') # add one
        browser.type("name", 'name')
        browser.type("age", '23')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_attribute('deformField6@name'), 'name')
        self.assertEqual(browser.get_value('deformField6'), 'name')
        self.assertEqual(browser.get_attribute('deformField7@name'), 'age')
        self.assertEqual(browser.get_value('deformField7'), '23')
        captured = browser.get_text('css=#captured')
        captured = eval(captured)
        self.assertEqual(captured,
                         {'people': [{'name': 'name', 'age': 23}]})

        browser.click('deformField1-seqAdd') # add another
        name1 = 'dom=document.forms[0].name[0]'
        age1 = 'dom=document.forms[0].age[0]'
        name2 = 'dom=document.forms[0].name[1]'
        age2 = 'dom=document.forms[0].age[1]'
        browser.type(name1, 'name-changed')
        browser.type(age1, '24')
        browser.type(name2, 'name2')
        browser.type(age2, '26')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_attribute('deformField6@name'), 'name')
        self.assertEqual(browser.get_value('deformField6'), 'name-changed')
        self.assertEqual(browser.get_attribute('deformField7@name'), 'age')
        self.assertEqual(browser.get_value('deformField7'), '24')
        self.assertEqual(browser.get_attribute('deformField9@name'), 'name')
        self.assertEqual(browser.get_value('deformField9'), 'name2')
        self.assertEqual(browser.get_attribute('deformField10@name'), 'age')
        self.assertEqual(browser.get_value('deformField10'), '26')
        captured = browser.get_text('css=#captured')
        captured = eval(captured)

        self.assertEqual(
            captured,
            {'people': [{'name': 'name-changed', 'age': 24},
                        {'name': 'name2', 'age': 26}]})

        browser.click('deformField5-close') # remove the first mapping
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_attribute('deformField6@name'), 'name')
        self.assertEqual(browser.get_value('deformField6'), 'name2')
        self.assertEqual(browser.get_attribute('deformField7@name'), 'age')
        self.assertEqual(browser.get_value('deformField7'), '26')

        captured = browser.get_text('css=#captured')
        captured = eval(captured)

        self.assertEqual(
            captured,
            {'people': [{'name': 'name2', 'age': 26}]})


class SequenceOfMappingsWithInitialItem(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings_with_initial_item/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_element_present('css=.deformProto'))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Person')
        self.assertEqual(browser.get_attribute('css=#deformField6@name'),
                         'name')
        self.assertEqual(browser.get_attribute('css=#deformField7@name'),
                         'age')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Person')
        self.assertEqual(browser.get_text('css=#error-deformField6'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField7'),
                         'Required')
        self.assertEqual(browser.get_text('css=#captured'), "None")
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_add_one(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.type("dom=document.forms[0].name[0]", 'name0')
        browser.type("dom=document.forms[0].age[0]", '23')
        browser.type("dom=document.forms[0].name[1]", 'name1')
        browser.type("dom=document.forms[0].age[1]", '25')
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Person')
        self.assertEqual(browser.get_attribute('css=#deformField6@name'),
                         'name')
        self.assertEqual(browser.get_attribute('css=#deformField6@value'),
                         'name0')
        self.assertEqual(browser.get_attribute('css=#deformField7@name'),
                         'age')
        self.assertEqual(browser.get_attribute('css=#deformField7@value'),
                         '23')
        self.assertEqual(browser.get_attribute('css=#deformField9@name'),
                         'name')
        self.assertEqual(browser.get_attribute('css=#deformField9@value'),
                         'name1')
        self.assertEqual(browser.get_attribute('css=#deformField10@name'),
                         'age')
        self.assertEqual(browser.get_attribute('css=#deformField10@value'),
                         '25')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertEqual(eval(captured),
                         {'people': [{'name': 'name0', 'age': 23},
                                     {'name': 'name1', 'age': 25}]}
                         )

class SequenceOfAutocompletes(Base, unittest.TestCase):
    url = test_url('/sequence_of_autocompletes/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Texts"))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        
    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), "{'texts': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_two_filled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        added = 'dom=document.forms[0].text'
        self.assertEqual(browser.get_attribute(added + '@class'),
                         'form-control  tt-query')
        browser.type(added, 'bar')
        browser.click('deformField1-seqAdd')
        added = 'dom=document.forms[0].text[1]'
        self.assertEqual(browser.get_attribute(added + '@class'),
                         'form-control  tt-query')
        browser.type(added, 'baz')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,  
            "{'texts': [u'bar', u'baz']}")

class SequenceOfDateInputs(Base, unittest.TestCase):
    url = test_url('/sequence_of_dateinputs/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Dates"))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Date')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        
    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Date')
        self.assertEqual(browser.get_text('css=#captured'), "{'dates': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_one_filled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        added = 'dom=document.forms[0].date'
        browser.focus(added)
        browser.click(added)
        browser.click('link=6')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertTrue(captured.startswith(u"{'dates': [datetime.date"))

class SequenceOfConstrainedLength(Base, unittest.TestCase):
    url = test_url('/sequence_of_constrained_len/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("At Least 2"))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Name')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        # default 2 inputs rendered
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertEqual(browser.get_value('deformField4'), '')

    def test_add_and_remove(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Name')
        self.assertTrue(browser.is_visible('deformField1-seqAdd'))
        browser.type('deformField3', 'hello1')
        browser.type('deformField4', 'hello2')
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.type('dom=document.forms[0].elements[6]', 'hello3')
        browser.type('dom=document.forms[0].elements[7]', 'hello4')
        self.assertFalse(browser.is_visible('deformField1-seqAdd'))
        browser.click('deformField3-close')
        self.assertTrue(browser.is_visible('deformField1-seqAdd'))
        browser.click('deformField1-seqAdd')
        self.assertFalse(browser.is_visible('deformField1-seqAdd'))
        browser.type('dom=document.forms[0].elements[7]', 'hello5')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField3'), 'hello2')
        self.assertEqual(browser.get_value('deformField4'), 'hello3')
        self.assertEqual(browser.get_value('deformField5'), 'hello4')
        self.assertEqual(browser.get_value('deformField6'), 'hello5')
        self.assertFalse(browser.is_visible('deformField1-seqAdd'))
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,
            "{'names': [u'hello2', u'hello3', u'hello4', u'hello5']}")
        
class SequenceOfRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_richtext/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Texts"))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        
    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), "{'texts': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_one_filled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.wait_for_condition(\
            "selenium.browserbot.getCurrentWindow().document"
            ".getElementsByTagName('iframe')[0]", "10000")
        browser.type('tinymce', 'yo')
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            "{'texts': [u'<p>yo</p>']}")

class SequenceOfMaskedTextInputs(Base, unittest.TestCase):
    url = test_url("/sequence_of_masked_textinputs/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Texts"))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        
    def test_submit_none_added(self):
        browser.get(self.url)
        browser.click("submit")
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Text')
        self.assertEqual(browser.get_text('css=#captured'), "{'texts': []}")
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_two_unfilled(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField1-seqAdd')
        browser.click("submit")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_one_filled(self):
        import time
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        added = 'dom=document.forms[0].text'
        browser.focus(added)
        for key in '140118866':
            browser.key_press(added, key)
            time.sleep(.005)
        browser.click("submit")
        self.assertFalse(browser.is_element_present('css=.has-error'))
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,  "{'texts': [u'140-11-8866']}"
            )

class SelectWidgetTests(Base, unittest.TestCase):
    url = test_url("/select/")
    submit_selected_captured = (
        "{'pepper': u'habanero'}",
        "{'pepper': 'habanero'}",
        )

    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Pepper"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'pepper')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        options = browser.get_select_options('deformField1')
        self.assertEqual(
            options,
            [u'- Select -', u'Habanero', u'Jalapeno', u'Chipotle']) 
        self.assertEqual(browser.get_text('css=.required'), 'Pepper')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_default(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_text_present("Pepper"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'pepper')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_selected(self):
        browser.get(self.url)
        browser.select('deformField1', 'index=1')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_selected_index('deformField1'), '1')
        captured = browser.get_text('css=#captured')
        self.assertTrue(captured in self.submit_selected_captured)

class SelectWidgetWithSizeTests(SelectWidgetTests):
    url = test_url("/select_with_size/")

class SelectWidgetWithUnicodeTests(SelectWidgetTests):
    url = test_url('/select_with_unicode/')
    submit_selected_captured = (
        u"{'pepper': '\u30cf\u30d0\u30cd\u30ed'}",
        u"{'pepper': u'\\u30cf\\u30d0\\u30cd\\u30ed'}",
        )

class SelectWidgetMultipleTests(Base, unittest.TestCase):
    url = test_url('/select_with_multiple/')

    def test_submit_selected(self):
        browser.get(self.url)

        captured_default = "{'pepper': set([u'chipotle', u'habanero'])}"

        browser.add_selection('deformField1', 'index=0')
        browser.add_selection('deformField1', 'index=2')

        browser.click('submit')

        captured = browser.get_text('css=#captured')

        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(captured, captured_default)

class SelectWidgetIntegerTests(Base, unittest.TestCase):
    url = test_url('/select_integer/')
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Number"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'number')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        options = browser.get_select_options('deformField1')
        self.assertEqual(
            options,
            [u'- Select -', u'Zero', u'One', u'Two']) 
        self.assertEqual(browser.get_text('css=.required'), 'Number')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_default(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_text_present("Number"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'number')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_selected(self):
        browser.get(self.url)
        browser.select('deformField1', 'index=1')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_selected_index('deformField1'), '1')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            "{'number': 0}")

class SelectWidgetWithOptgroupTest(Base, unittest.TestCase):
    url = test_url("/select_with_optgroup/")

    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present('Musician'))
        self.assertEqual(browser.get_attribute('deformField1@name'), 'musician')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        options = browser.get_select_options('deformField1')
        self.assertEqual(
            options,
            [u'Select your favorite musician',
             u'Jimmy Page', u'Jimi Hendrix', u'Billy Cobham', u'John Bonham']) 
        self.assertEqual(browser.get_text('css=.required'), 'Musician')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertEqual(int(browser.get_xpath_count('//optgroup')), 2)

    def test_submit_selected(self):
        browser.get(self.url)
        browser.select('deformField1', 'index=1')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_selected_index('deformField1'), '1')
        captured = browser.get_text('css=#captured')
        # With or without "u"...
        expected = ("{'musician': 'page'}", "{'musician': u'page'}")
        self.assertTrue(captured in expected)

class SelectWidgetWithOptgroupAndLabelTest(SelectWidgetWithOptgroupTest):
    url = test_url("/select_with_optgroup_and_label_attributes/")

    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present('Musician'))
        self.assertEqual(browser.get_attribute('deformField1@name'), 'musician')
        self.assertEqual(browser.get_selected_index('deformField1'), '0')
        # We cannot test what the options look like because it depends
        # on the browser.
        self.assertEqual(browser.get_text('css=.required'), 'Musician')
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertEqual(int(browser.get_xpath_count('//optgroup')), 2)

    def test_submit_selected(self):
        browser.get(self.url)
        browser.select('deformField1', 'index=1')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_selected_index('deformField1'), '1')
        captured = browser.get_text('css=#captured')
        expected = ("{'musician': 'page'}", "{'musician': u'page'}")
        self.assertTrue(captured in expected)

class TextInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Text"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'text')
        self.assertEqual(browser.get_attribute("deformField1@type"), 'text')
        self.assertEqual(browser.get_value("deformField1"), '')
        self.assertEqual(browser.get_text('css=.required'), 'Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_filled(self):
        browser.get(self.url)
        browser.type('deformField1', 'hello')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), 'hello')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            "{'text': u'hello'}")

class MoneyInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/money_input/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Greenbacks"))
        self.assertEqual(browser.get_attribute("deformField1@name"),
                         'greenbacks')
        self.assertEqual(browser.get_attribute("deformField1@type"), 'text')
        self.assertEqual(browser.get_value("deformField1"), '0.00')
        self.assertEqual(browser.get_text('css=.required'), 'Greenbacks')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(captured, "{'greenbacks': Decimal('0.00')}")

    def test_submit_filled(self):
        browser.get(self.url)
        browser.focus('deformField1')
        browser.type('deformField1', '100')
        browser.click('submit')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(captured, "{'greenbacks': Decimal('100')}")
        self.assertEqual(browser.get_value('deformField1'), '100')
        self.assertFalse(browser.is_element_present('css=.has-error'))

class TextInputWithCssClassWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput_with_css_class/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_element_present('css=.deformWidgetWithStyle'))

class AutocompleteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_input/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Autocomplete Input Widget"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'text')
        self.assertEqual(browser.get_attribute("deformField1@type"), 'text')
        self.assertEqual(browser.get_value("deformField1"), '')
        self.assertEqual(browser.get_text('css=.required'), 'Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_filled(self):
        browser.get(self.url)
        browser.focus('deformField1')
        browser.type('deformField1', 'bar')
        browser.type_keys('deformField1', 'bar')
        import time
        time.sleep(.5)
        self.assertTrue(browser.is_text_present('bar'))
        self.assertTrue(browser.is_text_present('baz'))
        browser.mouse_over("css=.tt-suggestion")
        browser.click("css=.tt-suggestion")
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), u'bar')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            "{'text': u'bar'}")

class AutocompleteRemoteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_remote_input/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present(
                "Autocomplete Input Widget (with Remote Data Source)"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'text')
        self.assertEqual(browser.get_attribute("deformField1@type"), 'text')
        self.assertEqual(browser.get_value("deformField1"), '')
        self.assertEqual(browser.get_text('css=.required'), 'Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_filled(self):
        browser.get(self.url)
        browser.focus('deformField1')
        browser.type('deformField1', 't')
        import time
        time.sleep(.5)
        browser.key_press('deformField1', 't')
        import time
        time.sleep(.5)
        import pdb;pdb.set_trace()
        self.assertTrue(browser.is_text_present('two'))
        self.assertTrue(browser.is_text_present('three'))
        browser.mouse_over("css=.tt-suggestion")
        browser.click("css=.tt-suggestion")
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), u'two')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,
            "{'text': u'two'}")

class TextAreaWidgetTests(Base, unittest.TestCase):
    url = test_url("/textarea/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Text"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'text')
        self.assertEqual(browser.get_attribute("deformField1@rows"), '10')
        self.assertEqual(browser.get_attribute("deformField1@cols"), '60')
        self.assertEqual(browser.get_value("deformField1"), '')
        self.assertEqual(browser.get_text('css=.required'), 'Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_filled(self):
        browser.get(self.url)
        browser.type('deformField1', 'hello')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), 'hello')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,
            "{'text': u'hello'}"
            )

class DelayedRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/delayed_richtext/")

    def test_submit_filled(self):
        browser.get(self.url)
        browser.click('css=.tinymce-preload')
        browser.wait_for_condition(\
            "selenium.browserbot.getCurrentWindow().document"
            ".getElementsByTagName('iframe')[0]", "10000")
        browser.type('tinymce', 'hello')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), '<p>hello</p>')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured,
            "{'text': u'<p>hello</p>'}"
            )

class RichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/richtext/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Text"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'text')
        self.assertEqual(browser.get_value("deformField1"), '')
        self.assertEqual(browser.get_text('css=.required'), 'Text')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, 'None')

    def test_submit_filled(self):
        browser.get(self.url)
        browser.type('tinymce', 'hello')
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), '<p>hello</p>')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            "{'text': u'<p>hello</p>'}"
            )

class RichTextWidgetInternationalized(Base, unittest.TestCase):
    url = test_url("/richtext_i18n/?_LOCALE_=ru")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Text"))
        self.assertTrue(browser.is_text_present(u"Формат"))

class UnicodeEverywhereTests(Base, unittest.TestCase):
    url = test_url("/unicodeeverywhere/")
    def test_render_default(self):
        browser.get(self.url)
        description=(u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？ "
                     u"人不知而不慍，不亦君子乎？」")

        self.assertTrue(browser.is_text_present(u"По оживлённым берегам"))
        self.assertEqual(browser.get_attribute("item-deformField1@title"),
                         description)
        self.assertEqual(browser.get_attribute("css=label@title"),
                         description)
        self.assertEqual(browser.get_attribute("deformField1@name"), 'field')
        self.assertEqual(browser.get_value("deformField1"), u'☃')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'), u'☃')
        captured = browser.get_text('css=#captured')
        self.assertTrue(
            captured in (
                u"{'field': u'\\u2603'}", # py2
                u"{'field': '\u2603'}",  # py3
            )
            )

class SequenceOfSequences(Base, unittest.TestCase):
    url = test_url("/sequence_of_sequences/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_text('deformField1-addtext'),
                         'Add Names and Titles')
        self.assertEqual(browser.get_text('deformField6-addtext'),
                         'Add Name and Title')
        self.assertEqual(browser.get_value('deformField21'), '')
        self.assertEqual(browser.get_value('deformField22'), '')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_add_two(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click('deformField6-seqAdd')
        browser.type('dom=document.forms[0].name[0]', 'name')
        browser.type('dom=document.forms[0].title[0]', 'title')
        browser.type('dom=document.forms[0].name[1]', 'name')
        browser.type('dom=document.forms[0].title[1]', 'title')
        browser.type('dom=document.forms[0].name[2]', 'name')
        browser.type('dom=document.forms[0].title[2]', 'title')
        browser.click("submit")
        captured = eval(browser.get_text('css=#captured'))
        self.assertEqual(captured,
                         {'names_and_titles_sequence': [
                             [{'name': u'name', 'title': u'title'},
                              {'name': u'name', 'title': u'title'}],
                             [{'name': u'name', 'title': u'title'}]]}
                         )

    def test_remove_from_nested_mapping_sequence(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.click("document.getElementsByClassName('deformClosebutton')[2]")
        self.assertFalse(browser.is_element_present('dom=document.forms[0].name[1]'))

class SequenceOrderable(Base, unittest.TestCase):
    url = test_url("/sequence_orderable/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_element_present('css=.deformProto'))
        self.assertEqual(browser.get_text('deformField1-addtext'),'Add Person')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_complex_interaction(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd') # add one
        # A single item shouldn't have an active reorder button.
        self.assertEqual(int(browser.get_xpath_count(
            "//span[@class='deformOrderbutton close glyphicon "
            "glyphicon-resize-vertical']")), 1)
        order1_style = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[0]@style")
        self.assertEqual(order1_style, 'display: none;')
        browser.click('deformField1-seqAdd') # add a second
        # Now there should be 2 active reorder buttons.
        self.assertEqual(int(browser.get_xpath_count(
            "//span[@class='deformOrderbutton close glyphicon "
            "glyphicon-resize-vertical']")), 2)
        order1_style = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[0]@style")
        self.assertEqual(order1_style, 'display: block;')
        order2_style = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[1]@style")
        self.assertEqual(order2_style, ';')
        browser.click('deformField1-seqAdd') # add a third

        browser.type("document.forms[0].name[0]", 'Name1')
        browser.type("document.forms[0].age[0]", '11')
        browser.type("document.forms[0].name[1]", 'Name2')
        browser.type("document.forms[0].age[1]", '22')
        browser.type("document.forms[0].name[2]", 'Name3')
        browser.type("document.forms[0].age[2]", '33')

        order1_id = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[0]@id")
        order2_id = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[1]@id")
        order3_id = browser.get_attribute(
            "document.getElementsByClassName('deformOrderbutton')[2]@id")

        # Determine the number of pixels between two order buttons.
        # We'll use this value later in calls to drag_and_drop().
        order1_top = int(browser.get_element_position_top(order1_id))
        order2_top = int(browser.get_element_position_top(order2_id))
        vertical_offset = order2_top - order1_top

        # Move item 1 down one slot (actually a little more than 1 is
        # needed to trigger jQuery Sortable when dragging down, so use 1.5).
        browser.drag_and_drop( order1_id,  "0,+%s" % (1.5 * vertical_offset))

        # Move item 3 up two
        browser.drag_and_drop( order3_id,  "0,-%s" % (2 * vertical_offset))

        browser.click("submit")

        # Original 3 items should now be in reverse order: 3, 2, 1

        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('document.forms[0].name[0]'),
                         'Name3')
        self.assertEqual(browser.get_value('document.forms[0].age[0]'),
                         '33')
        self.assertEqual(browser.get_value('document.forms[0].name[1]'),
                         'Name2')
        self.assertEqual(browser.get_value('document.forms[0].age[1]'),
                         '22')
        self.assertEqual(browser.get_value('document.forms[0].name[2]'),
                         'Name1')
        self.assertEqual(browser.get_value('document.forms[0].age[2]'),
                         '11')

        captured = browser.get_text('css=#captured')
        captured = eval(captured)
        self.assertEqual(captured, {'people': [
            {'name': 'Name3', 'age': 33},
            {'name': 'Name2', 'age': 22},
            {'name': 'Name1', 'age': 11},
        ]})

class TextAreaCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textareacsv/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Csv"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'csv')
        self.assertEqual(browser.get_attribute("deformField1@rows"), '10')
        self.assertEqual(browser.get_attribute("deformField1@cols"), '60')
        self.assertEqual(browser.get_value("deformField1"),
                         '1,hello,4.5\n2,goodbye,5.5')
        self.assertEqual(browser.get_text('css=.required'), 'Csv')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_default(self):
        from decimal import Decimal
        browser.get(self.url)
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'),
                         '1,hello,4.5\n2,goodbye,5.5')
        captured = browser.get_text('css=#captured')
        self.assertEqual(
            eval(captured),
            ({'csv': [(1, u'hello', Decimal("4.5")), 
                      (2, u'goodbye', Decimal("5.5"))]
              }))

    def test_submit_line_error(self):
        browser.get(self.url)
        browser.type('deformField1', '1,2,3\nwrong')
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertSimilarRepr(browser.get_text(error_node),
                         ('line 2: {\'1\': u\'"[\\\'wrong\\\']" has an '
                          'incorrect number of elements (expected 3, was 1)\'}')
                         )
        self.assertEqual(browser.get_value('deformField1'), '1,2,3\nwrong')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, "None")

    def test_submit_empty(self):
        browser.get(self.url)
        browser.type('deformField1', '')
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node), 'Required')
        self.assertEqual(browser.get_value('deformField1'), '')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, "None")

class TextInputCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinputcsv/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertTrue(browser.is_text_present("Csv"))
        self.assertEqual(browser.get_attribute("deformField1@name"), 'csv')
        self.assertEqual(browser.get_value("deformField1"),
                         '1,hello,4.5')
        self.assertEqual(browser.get_text('css=.required'), 'Csv')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_default(self):
        from decimal import Decimal
        browser.get(self.url)
        browser.click('submit')
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_value('deformField1'),
                         '1,hello,4.5')
        captured = browser.get_text('css=#captured')
        self.assertEqual(
            eval(captured),
            ({'csv': (1, u'hello', Decimal("4.5"))}))

    def test_submit_line_error(self):
        browser.get(self.url)
        browser.type('deformField1', '1,2,wrong')
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertSimilarRepr(
            browser.get_text(error_node),
            u'{\'2\': u\'"wrong" is not a number\'}'
            )
        self.assertEqual(browser.get_value('deformField1'), '1,2,wrong')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, "None")

    def test_submit_empty(self):
        browser.get(self.url)
        browser.type('deformField1', '')
        browser.click('submit')
        self.assertTrue(browser.is_element_present('css=.has-error'))
        error_node = 'css=#error-deformField1'
        self.assertEqual(browser.get_text(error_node), 'Required')
        self.assertEqual(browser.get_value('deformField1'), '')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, "None")

class WidgetAdapterTests(TextAreaCSVWidgetTests):
    url = test_url("/widget_adapter/")

class MultipleFormsTests(Base, unittest.TestCase):
    url = test_url("/multiple_forms/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_attribute("deformField1@name"), 'name1')
        self.assertEqual(browser.get_value('deformField1'), '')
        self.assertEqual(browser.get_attribute("deformField3@name"), 'name2')
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_first(self):
        browser.get(self.url)
        browser.type('deformField1', 'hey')
        browser.click('form1submit')
        self.assertEqual(browser.get_value('deformField1'), 'hey')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            u"{'name1': u'hey'}")

    def test_submit_second(self):
        browser.get(self.url)
        browser.type('deformField3', 'hey')
        browser.click('form2submit')
        self.assertEqual(browser.get_value('deformField3'), 'hey')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            u"{'name2': u'hey'}"
            )

class RequireOneFieldOrAnotherTests(Base, unittest.TestCase):
    url = test_url("/require_one_or_another/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertEqual(browser.get_attribute("deformField1@name"), 'one')
        self.assertEqual(browser.get_value('deformField1'), '')
        self.assertEqual(browser.get_attribute("deformField2@name"), 'two')
        self.assertEqual(browser.get_value('deformField2'), '')
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_submit_none_filled(self):
        browser.get(self.url)
        browser.click('submit')
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required if two is not supplied')
        self.assertEqual(browser.get_text('css=#error-deformField2'),
                         'Required if one is not supplied')
        captured = browser.get_text('css=#captured')
        self.assertEqual(captured, u"None")
        self.assertTrue(browser.is_element_present('css=.has-error'))

    def test_submit_one_filled(self):
        browser.get(self.url)
        browser.type('deformField1', 'one')
        browser.click('submit')
        captured = browser.get_text('css=#captured')
        self.assertSimilarRepr(
            captured, 
            u"{'one': u'one', 'two': u''}"
            )
        self.assertFalse(browser.is_element_present('css=.has-error'))

class AjaxFormTests(Base, unittest.TestCase):
    url = test_url("/ajaxform/")
    def test_render_default(self):
        browser.get(self.url)
        self.assertFalse(browser.is_element_present('css=.has-error'))
        self.assertTrue(browser.is_element_present('css=#req-deformField1'))
        self.assertTrue(browser.is_element_present('css=#req-deformField3'))
        self.assertTrue(browser.is_element_present('css=#req-deformField4'))
        self.assertEqual(browser.get_text('css=#captured'), 'None')
        self.assertEqual(browser.get_value('deformField1'), '')
        self.assertEqual(browser.get_attribute('deformField1@name'), 'number')
        self.assertEqual(browser.get_value('deformField3'), '')
        self.assertEqual(browser.get_attribute('deformField3@name'), 'name')
        self.assertEqual(browser.get_value('deformField4'), '')
        self.assertEqual(browser.get_attribute('deformField4@name'), 'year')
        self.assertEqual(browser.get_value('deformField4-month'), '')
        self.assertEqual(browser.get_attribute('deformField4-month@name'),
                         'month')
        self.assertEqual(browser.get_value('deformField4-day'), '')
        self.assertEqual(browser.get_attribute('deformField4-day@name'),
                         'day')
        self.assertEqual(browser.get_text('css=#captured'), 'None')

    def test_submit_empty(self):
        browser.get(self.url)
        browser.click('submit')
        browser.wait_for_condition(
            'selenium.browserbot.getCurrentWindow().jQuery.active == 0',
            "30000")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        self.assertEqual(browser.get_text('css=#captured'),
                         'None')

    def test_submit_invalid(self):
        browser.get(self.url)
        browser.type('deformField1', 'notanumber')
        browser.click('submit')
        browser.wait_for_condition(
            'selenium.browserbot.getCurrentWindow().jQuery.active == 0',
            "30000")
        self.assertTrue(browser.is_element_present('css=.has-error'))
        self.assertEqual(browser.get_text('css=#error-deformField1'),
                         '"notanumber" is not a number')
        self.assertEqual(browser.get_text('css=#error-deformField3'),
                         'Required')
        self.assertEqual(browser.get_text('css=#error-deformField4'),
                         'Required')
        self.assertEqual(browser.get_text('css=#captured'),
                         'None')

    def test_submit_success(self):
        browser.get(self.url)
        browser.type('deformField1', '1')
        browser.type('deformField3', 'name')
        browser.type('deformField4', '2010')
        browser.type('deformField4-month', '1')
        browser.type('deformField4-day', '1')
        browser.type('deformField5', 'text')
        browser.click('submit')
        browser.wait_for_condition(
            'selenium.browserbot.getCurrentWindow().jQuery.active == 0',
            "30000")
        self.assertEqual(browser.get_text('css=#thanks'), 'Thanks!')

class RedirectingAjaxFormTests(AjaxFormTests):
    url = test_url("/ajaxform_redirect/")
    def test_submit_success(self):
        import time
        browser.get(self.url)
        browser.type('deformField1', '1')
        browser.type('deformField3', 'name')
        browser.type('deformField4', '2010')
        browser.type('deformField4-month', '1')
        browser.type('deformField4-day', '1')
        browser.click('submit')
        time.sleep(1)
        ## browser.wait_for_condition(
        ##     'selenium.browserbot.getCurrentWindow().jQuery.active == 0',
        ##     "30000")
        location = browser.get_location()
        self.assertTrue(location.endswith('thanks.html'))

class TextInputMaskTests(Base, unittest.TestCase):
    url = test_url("/text_input_masks/")
    def test_render_default(self):
        browser.get(self.url)
        browser.focus('deformField1')
        self.assertEqual(browser.get_attribute("deformField1@name"), 'ssn')
        self.assertEqual(browser.get_value('deformField1'), '___-__-____')
        self.assertEqual(browser.get_attribute("deformField2@name"), 'date')
        self.assertEqual(browser.get_value('deformField2'), '')
        self.assertFalse(browser.is_element_present('css=.has-error'))

    def test_type_bad_input(self):
        import time
        browser.get(self.url)
        browser.focus('deformField1')
        browser.key_press('deformField1', 'a')
        time.sleep(.005)
        browser.focus('deformField2')
        browser.key_press('deformField2', 'a')
        time.sleep(.005)
        self.assertTrue(
            browser.get_value('deformField1') in ('', '___-__-____'))
        self.assertTrue(
            browser.get_value('deformField2') in ('', '__/__/____'))

    def test_submit_success(self):
        import time
        browser.get(self.url)
        browser.focus('deformField1')
        for key in '140118866':
            browser.key_press('deformField1', key)
            time.sleep(.005)
        browser.focus('deformField2')
        time.sleep(1)
        for key in '10102010':
            browser.key_press('deformField2', key)
            time.sleep(.005)
        browser.click('submit')
        self.assertSimilarRepr(
            browser.get_text('css=#captured'),
            u"{'date': u'10/10/2010', 'ssn': u'140-11-8866'}"
            )

class MultipleErrorMessagesInMappingTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_mapping/")
    def test_it(self):
        browser.get(self.url)
        browser.type('deformField1', 'whatever')
        browser.click('submit')
        self.assertEqual(browser.get_text('error-deformField1'), 'Error 1')
        self.assertEqual(browser.get_text('error-deformField1-1'), 'Error 2')
        self.assertEqual(browser.get_text('error-deformField1-2'), 'Error 3')

class MultipleErrorMessagesInSequenceTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_seq/")
    def test_it(self):
        browser.get(self.url)
        browser.click('deformField1-seqAdd')
        browser.type('dom=document.forms[0].field', 'whatever')
        browser.click('submit')
        self.assertEqual(browser.get_text('error-deformField3'), 'Error 1')
        self.assertEqual(browser.get_text('error-deformField3-1'), 'Error 2')
        self.assertEqual(browser.get_text('error-deformField3-2'), 'Error 3')

class CssClassesOnTheOutermostHTMLElement(Base, unittest.TestCase):
    url = test_url("/custom_classes_on_outermost_html_element/")
    def test_it(self):
        browser.get(self.url)
        self.assertTrue(browser.is_element_present('css=form > fieldset > ul > li.field.top_level_mapping_widget_custom_class'))
        self.assertTrue(browser.is_element_present('css=[title=SequenceWidget] > .deformSeq > ul > li.sequenced_widget_custom_class'))
        self.assertTrue(browser.is_element_present('css=[title=MappingWidget] > fieldset > ul > li.mapped_widget_custom_class'))
        

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()

# -*- coding: utf-8 -*-

import unittest
import re
import os
import time
from decimal import Decimal

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

# to run:
# console 1: java -jar selenium-server.jar
# console 2: start the deform demo server (pserve demo.ini)
# console 3: nosetests

# Note that this test file does not run under Python 3, but it can be used
# to test a deformdemo *instance* running under Python 3.

# Instead of using -browserSessionReuse as an arg to
# selenium-server.jar to speed up tests, we rely on
# setUpModule/tearDownModule functionality.

browser = None

BASE_PATH = os.environ.get('BASE_PATH', '')
URL = os.environ.get('URL', 'http://localhost:8522')

def findid(elid):
    return browser.find_element_by_id(elid)

def findcss(selector):
    return browser.find_element_by_css_selector(selector)

def findcsses(selector):
    return browser.find_elements_by_css_selector(selector)

def findxpath(selector):
    return browser.find_element_by_xpath(selector)

def findxpaths(selector):
    return browser.find_elements_by_xpath(selector)

def wait_for_ajax(source):
    def compare_source(driver):
        try:
            return source != driver.page_source
        except WebDriverException:
            pass

    WebDriverWait(browser, 5).until(compare_source)

def setUpModule():
    from selenium.webdriver import Firefox
    global browser
    browser = Firefox()
    return browser

def tearDownModule():
    browser.quit()

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
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findcss('.required').text, 'Pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_unchecked(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        error_node = 'error-deformField1'
        self.assertEqual(findid(error_node).text,
                         'Shorter than minimum length 1')
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertTrue(findid('deformField1-0').is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'habanero'}}",
            )

    def test_submit_three_checked(self):
        findid("deformField1-0").click()
        findid("deformField1-1").click()
        findid("deformField1-2").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertTrue(findid('deformField1-0').is_selected())
        self.assertTrue(findid('deformField1-1').is_selected())
        self.assertTrue(findid('deformField1-2').is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'chipotle', 'habanero', 'jalapeno'}}",
            )

class CheckboxChoiceWidgetInlineTests(Base, unittest.TestCase):
    url = test_url("/checkboxchoice_inline/")
    def test_render_default(self):
        self.assertTrue('Pepper' in browser.page_source)
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findcss('.required').text, 'Pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_unchecked(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        error_node = 'error-deformField1'
        self.assertEqual(findid(error_node).text,
                         'Shorter than minimum length 1')
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertTrue(findid('deformField1-0').is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'habanero'}}",
            )

    def test_submit_three_checked(self):
        findid("deformField1-0").click()
        findid("deformField1-1").click()
        findid("deformField1-2").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertTrue(findid('deformField1-0').is_selected())
        self.assertTrue(findid('deformField1-1').is_selected())
        self.assertTrue(findid('deformField1-2').is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            u"{'pepper': {'chipotle', 'habanero', 'jalapeno'}}",
            )
        
class CheckboxChoiceReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkboxchoice_readonly/")
    def test_render_default(self):
        self.assertTrue('Pepper' in browser.page_source)
        self.assertEqual(
            findid('deformField1-1').text,
            'Jalapeno'
            )
        self.assertEqual(
            findid('deformField1-2').text,
            'Chipotle'
            )
        self.assertEqual(findid('captured').text, 'None')

class CheckboxWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkbox/")
    def test_render_default(self):
        self.assertTrue('I Want It!' in browser.page_source)
        self.assertFalse(findid('deformField1').is_selected())
        self.assertEqual(findcss('.required').text, 'I Want It!')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_unchecked(self):
        findid("deformsubmit").click()
        self.assertFalse(findid('deformField1').is_selected())
        self.assertEqual(findid('captured').text, "{'want': False}")

    def test_submit_checked(self):
        findid("deformField1").click()
        findid("deformsubmit").click()
        self.assertTrue(findid('deformField1').is_selected())
        self.assertEqual(findid('captured').text, "{'want': True}")
    
class CheckboxReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkbox_readonly/")
    def test_render_default(self):
        self.assertTrue('I Want It!' in browser.page_source)
        self.assertEqual(
            findid('deformField1').text,
            'True'
            )
        self.assertEqual(findid('captured').text, 'None')
        
class CheckedInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedinput/")
    def test_render_default(self):
        self.assertTrue('Email Address' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Email Address')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            '')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_invalid(self):
        findid('deformField1').send_keys('this')
        findid('deformField1-confirm').send_keys('this')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text,
                         'Invalid email address')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'this')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'this'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_mismatch(self):
        findid('deformField1').send_keys('this@example.com')
        findid('deformField1-confirm').send_keys('that@example.com')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(
            findid('error-deformField1').text,
            'Fields did not match'
            )
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'this@example.com'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'that@example.com'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').send_keys('user@example.com')
        findid('deformField1-confirm').send_keys('user@example.com')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'user@example.com')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'user@example.com'
            )
        self.assertEqual(
            findid('captured').text,
            "{'email': u'user@example.com'}"
            )

class CheckedInputWidgetWithMaskTests(Base, unittest.TestCase):
    url = test_url("/checkedinput_withmask/")
    def test_render_default(self):
        self.assertEqual(findcss('.required').text, 'Social Security Number')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            '###-##-####'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            ''
            )
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_type_bad_input(self):
        findid('deformField1').send_keys('a')
        findid('deformField1-confirm').send_keys('a')
        self.assertTrue(
            findid('deformField1').get_attribute('value') in
            ('', '###-##-####')
            )
        self.assertTrue(
            findid('deformField1-confirm').get_attribute('value') in
            ('', '###-##-####')
            )

    def test_submit_success(self):
        findid('deformField1').send_keys('140118866')
        browser.execute_script(
            'document.getElementById("deformField1-confirm").focus();')
        findid('deformField1-confirm').send_keys('140118866')
        findid("deformsubmit").click()
        self.assertEqual(findid('captured').text, "{'ssn': u'140-11-8866'}")


class CheckedInputReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkedinput_readonly/")
    def test_render_default(self):
        self.assertTrue('Email Address' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Email Address')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1').text,
            'ww@graymatter.com'
            )
        
class CheckedPasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword/")
    def test_render_default(self):
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Password')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            ''
            )
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('type'),
            'password'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('type'),
            'password'
            )

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            ''
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_tooshort(self):
        findid('deformField1').send_keys('this')
        findid('deformField1-confirm').send_keys('this')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(
            findid('error-deformField1').text,
            'Shorter than minimum length 5'
            )
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'this'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'this'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_mismatch(self):
        findid('deformField1').send_keys('this123')
        findid('deformField1-confirm').send_keys('that123')
        findid("deformsubmit").click()
        self.assertEqual(
            findid('error-deformField1').text,
            'Password did not match confirm'
            )
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'this123'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'that123'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').send_keys('this123')
        findid('deformField1-confirm').send_keys('this123')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'this123'
            )
        self.assertEqual(
            findid('deformField1-confirm').get_attribute('value'),
            'this123'
            )
        self.assertEqual(findid('captured').text, "{'password': u'this123'}")

class CheckedPasswordReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword_readonly/")
    def test_render_default(self):
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Password')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1').text,
            'Password not displayed.'
            )

        
class DateInputWidgetTests(Base, unittest.TestCase):
    url = test_url('/dateinput/')
    def test_render_default(self):
        self.assertTrue('Date' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Date')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_tooearly(self):
        import datetime
        findid('deformField1').click()
        def diff_month(d1, d2):
            return (d1.year - d2.year)*12 + d1.month - d2.month
        tooearly = datetime.date(2010, 01, 01)
        today = datetime.date.today()
        num_months = diff_month(today, tooearly)
        [ findcss('.picker__nav--prev').click() for x in range(num_months) ]
        findcss(".picker__day").click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertTrue('is earlier than' in findid('error-deformField1').text)
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        import datetime
        today = datetime.date.today()
        findid('deformField1').click()
        findcss(".picker__button--today").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        expected = '%d, %d, %d' % (today.year, today.month, today.day)
        expected = "{'date': datetime.date(%s)}" % expected
        self.assertSimilarRepr(
            findid('captured').text,
            expected
            )


class TimeInputWidgetTests(Base, unittest.TestCase):
    url = test_url('/timeinput/')
    def test_render_default(self):
        self.assertTrue('Time' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Time')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1').get_attribute('value'), '14:35:00')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_empty(self):
        findid('deformField1').clear()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_tooearly(self):
        findid('deformField1').click()
        findxpath('//li[@data-pick="600"]').click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertTrue('is earlier than' in findid('error-deformField1').text)
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').click()
        findxpath('//li[@data-pick="900"]').click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        expected = "{'time': datetime.time(15, 0)}"
        captured = findid('captured').text
        if captured.startswith('u'):
            captured = captured[1:]
        self.assertEqual(captured, expected)


class DateTimeInputWidgetTests(Base, unittest.TestCase):
    url = test_url('/datetimeinput/')
    def test_render_default(self):
        self.assertEqual(findcss('.required').text, 'Date Time')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(
            findid('deformField1-date').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField1-time').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_both_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_time_empty(self):
        findid('deformField1-date').click()
        findcss(".picker__button--today").click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Incomplete time')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_date_empty(self):
        findid('deformField1-time').click()
        findxpath('//li[@data-pick="0"]').click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Incomplete date')
        self.assertEqual(findid('captured').text, 'None')
        
    def test_submit_tooearly(self):
        import datetime
        findid('deformField1-time').click()
        findxpath('//li[@data-pick="0"]').click()
        findid('deformField1-date').click()
        def diff_month(d1, d2):
            return (d1.year - d2.year)*12 + d1.month - d2.month
        tooearly = datetime.date(2010, 01, 01)
        today = datetime.date.today()
        num_months = diff_month(today, tooearly)
        [ findcss('.picker__nav--prev').click() for x in range(num_months) ]
        findcss(".picker__day").click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertTrue('is earlier than' in findid('error-deformField1').text)
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        import datetime
        now = datetime.datetime.utcnow()
        findid('deformField1-time').click()
        findxpath('//li[@data-pick="60"]').click()
        findid('deformField1-date').click()
        findcss(".picker__button--today").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        expected = '%d, %d, %d, %d, %d' % (
            now.year, now.month, now.day, 1, 0
            )
        expected = "{'date_time': datetime.datetime(%s" % expected
        captured = findid('captured').text
        if captured.startswith('u'):
            captured = captured[1:]
        self.assertTrue(
            captured.startswith(expected),
            (captured, expected)
            )

class DateTimeInputReadonlyTests(Base, unittest.TestCase):
    url = test_url('/datetimeinput_readonly/')
    def test_render_default(self):
        self.assertEqual(findcss('.required').text, 'Date Time')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').text, '2011-05-05 01:02:00')


class DatePartsWidgetTests(Base, unittest.TestCase):
    url = test_url('/dateparts/')
    def test_render_default(self):
        self.assertTrue('Date' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Date')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField1-month').get_attribute('value'),'')
        self.assertEqual(findid('deformField1-day').get_attribute('value'), '')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField1-month').get_attribute('value'),'')
        self.assertEqual(findid('deformField1-day').get_attribute('value'), '')
        self.assertTrue(findcss('.has-error'))

    def test_submit_only_year(self):
        findid('deformField1').send_keys('2010')
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Incomplete date')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '2010')
        self.assertEqual(findid('deformField1-month').get_attribute('value'),'')
        self.assertEqual(findid('deformField1-day').get_attribute('value'), '')
        self.assertTrue(findcss('.has-error'))

    def test_submit_only_year_and_month(self):
        findid('deformField1').send_keys('2010')
        findid('deformField1-month').send_keys('1')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Incomplete date')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '2010')
        self.assertEqual(
            findid('deformField1-month').get_attribute('value'),
            '1'
            )
        self.assertEqual(findid('deformField1-day').get_attribute('value'), '')

    def test_submit_tooearly(self):
        findid('deformField1').send_keys('2008')
        findid('deformField1-month').send_keys('1')
        findid('deformField1-day').send_keys('1')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text,
                         '2008-01-01 is earlier than earliest date 2010-01-01')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '2008')
        self.assertEqual(
            findid('deformField1-month').get_attribute('value'),
            '1'
            )
        self.assertEqual(
            findid('deformField1-day').get_attribute('value'),
            '1'
            )

    def test_submit_success(self):
        findid('deformField1').send_keys('2010')
        findid('deformField1-month').send_keys('1')
        findid('deformField1-day').send_keys('1')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text,
                         "{'date': datetime.date(2010, 1, 1)}")
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            '2010'
            )
        self.assertEqual(
            findid('deformField1-month').get_attribute('value'),
            '01'
            )
        self.assertEqual(
            findid('deformField1-day').get_attribute('value'),
            '01'
            )

class DatePartsReadonlyTests(Base, unittest.TestCase):
    url = test_url('/dateparts_readonly/')
    def test_render_default(self):
        self.assertTrue('Date' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Date')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').text, '2010/05/05')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        
class EditFormTests(Base, unittest.TestCase):
    url = test_url("/edit/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            '42'
            )
        self.assertEqual(
            findid('deformField1').get_attribute('name'),
            'number'
            )
        self.assertEqual(
            findid('deformField3').get_attribute('value'),
            ''
            )
        self.assertEqual(
            findid('deformField3').get_attribute('name'),
            'name'
            )
        self.assertEqual(
            findid('deformField4').get_attribute('value'),
            '2010'
            )
        self.assertEqual(
            findid('deformField4').get_attribute('name'),
            'year'
            )
        self.assertEqual(
            findid('deformField4-month').get_attribute('value'),
            '04'
            )
        self.assertEqual(
            findid('deformField4-month').get_attribute('name'),
            'month'
            )
        self.assertEqual(
            findid('deformField4-day').get_attribute('value'),
            '09'
            )
        self.assertEqual(
            findid('deformField4-day').get_attribute('name'),
            'day'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField3').send_keys('name')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            '42'
            )
        self.assertEqual(findid('deformField3').get_attribute('value'), 'name')
        self.assertEqual(findid('deformField4').get_attribute('value'), '2010')
        self.assertEqual(
            findid('deformField4-month').get_attribute('value'),
            '04'
            )
        self.assertEqual(
            findid('deformField4-day').get_attribute('value'),
            '09'
            )
        self.assertSimilarRepr(
            findid('captured').text,
            (u"{'mapping': {'date': datetime.date(2010, 4, 9), "
             "'name': u'name'}, 'number': 42}")
            )

class MappingWidgetTests(Base, unittest.TestCase):
    url = test_url("/mapping/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('deformField4').get_attribute('value'), '')
        self.assertEqual(findid('deformField4-month').get_attribute('value'),'')
        self.assertEqual(findid('deformField4-day').get_attribute('value'), '')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_invalid_number(self):
        findid('deformField1').send_keys('notanumber')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(
            findid('error-deformField1').text,
            '"notanumber" is not a number'
            )
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_invalid_date(self):
        findid('deformField1').send_keys('1')
        findid('deformField3').send_keys('name')
        findid('deformField4').send_keys('year')
        findid('deformField4-month').send_keys('month')
        findid('deformField4-day').send_keys('day')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField4').text, 'Invalid date')
        self.assertEqual(findid('deformField1').get_attribute('value'), '1')
        self.assertEqual(findid('deformField3').get_attribute('value'), 'name')
        self.assertEqual(findid('deformField4').get_attribute('value'), 'year')
        self.assertEqual(
            findid('deformField4-month').get_attribute('value'),
            'mo'
            )
        self.assertEqual(
            findid('deformField4-day').get_attribute('value'),
            'da'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').send_keys('1')
        findid('deformField3').send_keys('name')
        findid('deformField4').send_keys('2010')
        findid('deformField4-month').send_keys('1')
        findid('deformField4-day').send_keys('1')
        findid("deformsubmit").click()
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            '1'
            )
        self.assertEqual(
            findid('deformField3').get_attribute('value'),
            'name'
            )
        self.assertEqual(
            findid('deformField4').get_attribute('value'),
            '2010'
            )
        self.assertEqual(
            findid('deformField4-month').get_attribute('value'),
            '01'
            )
        self.assertEqual(
            findid('deformField4-day').get_attribute('value'),
            '01'
            )
        self.assertSimilarRepr(
            findid('captured').text,
            (u"{'mapping': {'date': datetime.date(2010, 1, 1), "
             "'name': u'name'}, 'number': 1}")
            )

class FieldDefaultTests(Base, unittest.TestCase):
    url = test_url("/fielddefaults/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'Grandaddy'
            )
        self.assertEqual(
            findid('deformField2').get_attribute('value'),
            'Just Like the Fambly Cat'
            )
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'Grandaddy'
            )
        self.assertEqual(
            findid('deformField2').get_attribute('value'),
            'Just Like the Fambly Cat'
            )
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('error-deformField3').text, 'Required')

    def test_submit_success(self):
        findid('deformField1').clear()
        findid('deformField1').send_keys('abc')
        findid('deformField2').clear()
        findid('deformField2').send_keys('def')
        findid('deformField3').clear()
        findid('deformField3').send_keys('ghi')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(findid('deformField2').get_attribute('value'), 'def')
        self.assertEqual(findid('deformField3').get_attribute('value'), 'ghi')
        self.assertSimilarRepr(
            findid('captured').text,
            u"{'album': u'def', 'artist': u'abc', 'song': u'ghi'}")

class NonRequiredFieldTests(Base, unittest.TestCase):
    url = test_url("/nonrequiredfields/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success_required_filled_notrequired_empty(self):
        findid('deformField1').send_keys('abc')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertSimilarRepr(
            findid('captured').text,
            u"{'notrequired': u'', 'required': u'abc'}")

    def test_submit_success_required_and_notrequired_filled(self):
        findid('deformField1').send_keys('abc')
        findid('deformField2').send_keys('def')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(findid('deformField2').get_attribute('value'), 'def')
        self.assertSimilarRepr(
            findid('captured').text,
            u"{'notrequired': u'def', 'required': u'abc'}")

class HiddenFieldWidgetTests(Base, unittest.TestCase):
    url = test_url("/hidden_field/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'true')
        self.assertEqual(findid('captured').text, 'None')

    def test_render_submitted(self):
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'true')
        self.assertEqual(findid('captured').text, "{'sneaky': True}")

class HiddenmissingTests(Base, unittest.TestCase):
    url = test_url("/hiddenmissing/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_render_submitted(self):
        findid('deformField1').send_keys('yup')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'yup')
        self.assertSimilarRepr(
            findid('captured').text,
            "{'number': <colander.null>, 'title': u'yup'}")

class FileUploadTests(Base, unittest.TestCase):
    url = test_url("/file/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_filled(self):
        # submit one first
        path, filename = _getFile()
        findid('deformField1').send_keys(path)
        findid("deformsubmit").click()

        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField1-filename').text, filename)
        self.assertTrue(filename in findid('captured').text)
        uid = findid('deformField1-uid').get_attribute('value')
        self.assertTrue(uid in findid('captured').text)

        # resubmit without entering a new filename should not change the file
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-filename').text, filename)
        self.assertEqual(findid('deformField1-uid').get_attribute('value'), uid)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile('selenium.py')
        findid('deformField1').send_keys(path2)
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-filename').text, filename2)
        self.assertTrue('filename' in findid('captured').text)
        self.assertTrue(uid in findid('captured').text)

class FileUploadReadonlyTests(Base, unittest.TestCase):
    url = test_url("/file_readonly/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').text, 'leavesofgrass.png')
        self.assertEqual(findid('captured').text, 'None')

        
class InterFieldValidationTests(Base, unittest.TestCase):
    url=  test_url("/interfield/")
    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_both_empty(self):
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('error-deformField2').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_empty(self):
        findid('deformField1').send_keys('abc')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        self.assertEqual(findid('error-deformField2').text, 'Required')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_first_doesnt_start_with_second(self):
        findid('deformField1').send_keys('abc')
        findid('deformField2').send_keys('def')
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        self.assertEqual(
            findid('error-deformField2').text,
            'Must start with name abc'
            )
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(findid('deformField2').get_attribute('value'), 'def')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').send_keys('abc')
        findid('deformField2').send_keys('abcdef')
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        self.assertRaises(NoSuchElementException, findid, 'error-deformField1')
        self.assertEqual(findid('deformField1').get_attribute('value'), 'abc')
        self.assertEqual(
            findid('deformField2').get_attribute('value'),
            'abcdef'
            )
        self.assertEqual(eval(findid('captured').text),
                         {'name': 'abc', 'title': 'abcdef'})

class InternationalizationTests(Base, unittest.TestCase):
    url = test_url("/i18n/")

    def setUp(self):
        pass  # each tests has a different url

    def test_render_default(self):
        browser.get(self.url)
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findcss('label').text, 'A number between 1 and 10')
        self.assertEqual(findid("deformsubmit").text, 'Submit')

    def test_render_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findcss('label').text, 'A number between 1 and 10')
        self.assertEqual(findid("deformsubmit").text, 'Submit')
    
    def test_render_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findcss('label').text, u'Число между 1 и 10')
        self.assertEqual(findid("deformsubmit").text, u'отправить')
    
    def test_submit_empty_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        findid("deformsubmit").click()
        self.assertEqual(
            findcss('.alert-danger').text,
            'There was a problem with your submission'
            )
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findcss('label').text, 'A number between 1 and 10')
        self.assertEqual(findid("deformsubmit").text, 'Submit')

    def test_submit_empty_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        findid("deformsubmit").click()
        self.assertEqual(
            findcss('.alert-danger').text,
            u'Данные которые вы предоставили содержат ошибку')
        self.assertEqual(findid('error-deformField1').text, u'Требуется')
        self.assertEqual(findcss('label').text, u'Число между 1 и 10')
        self.assertEqual(findid("deformsubmit").text, u'отправить')

    def test_submit_toolow_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        findid('deformField1').send_keys('0')
        findid("deformsubmit").click()
        self.assertEqual(
            findcss('.alert-danger').text,
            'There was a problem with your submission'
            )
        self.assertEqual(
            findid('error-deformField1').text,
            '0 is less than minimum value 1'
            )
        self.assertEqual(findcss('label').text, 'A number between 1 and 10')
        self.assertEqual(findid("deformsubmit").text, 'Submit')

    def test_submit_toolow_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        findid('deformField1').send_keys('0')
        findid("deformsubmit").click()
        self.assertEqual(
            findcss('.alert-danger').text,
            u'Данные которые вы предоставили содержат ошибку'
            )
        self.assertEqual(findid('error-deformField1').text, u'0 меньше чем 1')
        self.assertEqual(findcss('label').text, u'Число между 1 и 10')
        self.assertEqual(findid("deformsubmit").text, u'отправить')


class PasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/password/")
    def test_render_default(self):
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(findid('captured').text, 'None')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findcss('.required').text, 'Password')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')

    def test_render_submit_empty(self):
        findid("deformsubmit").click()
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(findcss('.required').text, 'Password')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('error-deformField1').text, 'Required')

    def test_render_submit_success(self):
        findid('deformField1').send_keys('abcdef123')
        findid("deformsubmit").click()
        self.assertTrue('Password' in browser.page_source)
        self.assertEqual(
            findid('deformField1').get_attribute('value'),
            'abcdef123'
            )
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertSimilarRepr(
            findid('captured').text,
            "{'password': u'abcdef123'}")

class RadioChoiceWidgetTests(Base, unittest.TestCase):
    url = test_url("/radiochoice/")
    def test_render_default(self):
        self.assertTrue('Password' in browser.page_source)
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findcss('.required').text, 'Choose your pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_unchecked(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_checked(self):
        findid('deformField1-0').click()
        findid("deformsubmit").click()
        self.assertTrue(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertSimilarRepr(
            findid('captured').text,
            "{'pepper': u'habanero'}")

class RadioChoiceWidgetInlineTests(Base, unittest.TestCase):
    url = test_url("/radiochoice_inline/")
    def test_render_default(self):
        self.assertTrue('Password' in browser.page_source)
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findcss('.required').text, 'Choose your pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_unchecked(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertFalse(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_checked(self):
        findid('deformField1-0').click()
        findid("deformsubmit").click()
        self.assertTrue(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertSimilarRepr(
            findid('captured').text,
            "{'pepper': u'habanero'}")
        
class RadioChoiceWidgetIntTests(RadioChoiceWidgetTests):
    url = test_url("/radiochoice_int/")
    def test_submit_one_checked(self):
        findid('deformField1-0').click()
        findid("deformsubmit").click()
        self.assertTrue(findid('deformField1-0').is_selected())
        self.assertFalse(findid('deformField1-1').is_selected())
        self.assertFalse(findid('deformField1-2').is_selected())
        self.assertSimilarRepr(
            findid('captured').text,
            "{'pepper': 0}")

class RadioChoiceReadonlyTests(Base, unittest.TestCase):
    url = test_url("/radiochoice_readonly/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1-1').text, 'Jalapeno')
        self.assertEqual(findcss('.required').text, 'Pepper')
        self.assertEqual(findid('captured').text, 'None')

class ReadOnlySequenceOfMappingTests(Base, unittest.TestCase):
    url = test_url("/readonly_sequence_of_mappings/")
    def test_render_default(self):
        self.assertEqual(findid('deformField6').text, 'name1')
        self.assertEqual(findid('deformField7').text, '23')
        self.assertEqual(findid('deformField9').text, 'name2')
        self.assertEqual(findid('deformField10').text, '25')

class SequenceOfRadioChoicesTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_radiochoices/")
    def test_render_default(self):
        self.assertEqual(
            findid('deformField1-addtext').text,
            'Add Pepper Chooser'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(
            findid('deformField1-addtext').text,
            'Add Pepper Chooser'
            )
        self.assertEqual(findid('captured').text, "{'peppers': []}")
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_two_filled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findxpaths('//input')[4].click()
        findxpaths('//input')[10].click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(eval(findid('captured').text),
                         {'peppers': ['habanero', 'jalapeno']})

class SequenceOfDefaultedSelectsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects/")
    def test_render_default(self):
        self.assertEqual(
            findid('deformField1-addtext').text,
            'Add Pepper Chooser'
            )
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(
            findid('deformField1-addtext').text,
            'Add Pepper Chooser'
            )
        self.assertEqual(findid('captured').text, "{'peppers': []}")
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_two_filled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            eval(findid('captured').text), # should be 2 values, both defaults
            {'peppers': ['jalapeno', 'jalapeno']}
            )

class SequenceOfDefaultedSelectsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects_with_initial_item/")
    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(
            findid('deformField1-addtext').text,
            'Add Pepper Chooser'
            )
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            eval(findid('captured').text), # should be 1 value (min_len 1)
            {'peppers': ['jalapeno']}
            )

    def test_submit_one_added(self):
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(
            eval(findid('captured').text), # should be 2 values, both defaults
            {'peppers': ['jalapeno', 'jalapeno']}
            )

class SequenceOfFileUploadsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1-addtext').text, 'Add Upload')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-addtext').text, 'Add Upload')
        self.assertEqual(findid('captured').text, "{'uploads': []}")
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_upload_one_success(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpath('//input[@name="upload"]').send_keys(path)
        findid("deformsubmit").click()

        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('deformField3-filename').text, filename)
        uid = findid('deformField3-uid').get_attribute('value')
        self.assertTrue(filename in findid('captured').text)
        self.assertTrue(uid in findid('captured').text)

    def test_upload_multi_interaction(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpath('//input[@name="upload"]').send_keys(path)
        findid("deformsubmit").click()

        self.assertRaises(NoSuchElementException, findcss, '.has-error')

        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('deformField3-filename').text, filename)
        uid = findid('deformField3-uid').get_attribute('value')
        self.assertTrue(filename in findid('captured').text)
        self.assertTrue(uid in findid('captured').text)

        # resubmit without entering a new filename should not change the file
        findid("deformsubmit").click()
        self.assertTrue(filename in findid('captured').text)
        self.assertTrue(uid in findid('captured').text)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile('selenium.py')
        findid('deformField3').send_keys(path2)
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField3-filename').text, filename2)
        self.assertTrue(filename2 in findid('captured').text)

        # add a new file
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="upload"]')[1].send_keys(path)
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField3-filename').text, filename2)
        self.assertEqual(findid('deformField4-filename').text, filename)

        # resubmit should not change either file
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField3-filename').text, filename2)
        self.assertEqual(findid('deformField4-filename').text, filename)

        # remove a file
        findid("deformField4-close").click()
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField3-filename').text, filename2)
        self.assertRaises(
            NoSuchElementException,
            findid,
            'deformField4-filename'
            )

class SequenceOfFileUploadsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads_with_initial_item/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1-addtext').text, 'Add Upload')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_upload_one_success(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="upload"]')[0].send_keys(path)
        findxpaths('//input[@name="upload"]')[1].send_keys(path)
        findid("deformsubmit").click()

        # first element present
        self.assertEqual(findid('deformField3-filename').text, filename)
        uid = findid('deformField3-uid').get_attribute('value')
        self.assertTrue(uid in findid('captured').text)

        # second element present
        self.assertEqual(findid('deformField4-filename').text, filename)
        uid = findid('deformField4-uid').get_attribute('value')
        self.assertTrue(uid in findid('captured').text)

class SequenceOfMappingsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1-addtext').text, 'Add Person')
        self.assertEqual(findid('captured').text, 'None')
        self.assertTrue(findcss('.deformProto'))

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-addtext').text, 'Add Person')
        self.assertEqual(findid('captured').text, "{'people': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField6').text, 'Required')
        self.assertEqual(findid('error-deformField7').text, 'Required')
        self.assertEqual(findid('error-deformField9').text, 'Required')
        self.assertEqual(findid('error-deformField10').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_complex_interaction(self):
        findid("deformField1-seqAdd").click()
        findid('deformField1').send_keys('abcdef123')
        findxpath('//input[@name="name"]').send_keys('name')
        findxpath('//input[@name="age"]').send_keys('23')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'people': [{'name': 'name', 'age': 23}]})

        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].clear()
        findxpaths('//input[@name="name"]')[0].send_keys('name-changed')
        findxpaths('//input[@name="name"]')[1].send_keys('name2')
        findxpaths('//input[@name="age"]')[0].clear()
        findxpaths('//input[@name="age"]')[0].send_keys('24')
        findxpaths('//input[@name="age"]')[1].send_keys('26')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
            {'people': [{'name': 'name-changed', 'age': 24},
                        {'name': 'name2', 'age': 26}]})

        findid("deformField5-close").click() # remove the first mapping
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
            {'people': [{'name': 'name2', 'age': 26}]})


class SequenceOfMappingsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings_with_initial_item/")
    def test_render_default(self):
        self.assertTrue(findcss('.deformProto'))
        self.assertEqual(findid('deformField1-addtext').text, 'Add Person')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField6').text, 'Required')
        self.assertEqual(findid('error-deformField7').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_add_one(self):
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].send_keys('name0')
        findxpaths('//input[@name="name"]')[1].send_keys('name1')
        findxpaths('//input[@name="age"]')[0].send_keys('23')
        findxpaths('//input[@name="age"]')[1].send_keys('25')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'people': [{'name': 'name0', 'age': 23},
                                     {'name': 'name1', 'age': 25}]})

class SequenceOfAutocompletes(Base, unittest.TestCase):
    url = test_url('/sequence_of_autocompletes/')
    def test_render_default(self):
        self.assertEqual(findid('captured').text, 'None')
        self.assertTrue('Texts' in browser.page_source)
        self.assertEqual(findid('deformField1-addtext').text, 'Add Text')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-addtext').text, 'Add Text')
        self.assertEqual(findid('captured').text, "{'texts': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_two_filled(self):
        findid("deformField1-seqAdd").click()
        self.assertEqual(
            findxpaths('//input[@name="text"]')[0].get_attribute('class'),
            'form-control  tt-query'
            )
        findxpaths('//input[@name="text"]')[0].send_keys('bar')

        findid("deformField1-seqAdd").click()
        self.assertEqual(
            findxpaths('//input[@name="text"]')[1].get_attribute('class'),
            'form-control  tt-query'
            )
        findxpaths('//input[@name="text"]')[1].send_keys('baz')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'texts': [u'bar', u'baz']})

class SequenceOfDateInputs(Base, unittest.TestCase):
    url = test_url('/sequence_of_dateinputs/')
    def test_render_default(self):
        self.assertTrue('Dates' in browser.page_source)
        self.assertEqual(findid('deformField1-addtext').text, 'Add Date')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-addtext').text, 'Add Date')
        self.assertSimilarRepr(
            findid('captured').text,
            "{'dates': []}"
            )
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')
        
    def test_submit_one_filled(self):
        findid("deformField1-seqAdd").click()
        findcss('input[type="text"]').click()
        findcss(".picker__button--today").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertTrue(
            findid('captured').text.startswith("{'dates': [datetime.date")
            )
        
class SequenceOfConstrainedLengthTests(Base, unittest.TestCase):
    url = test_url('/sequence_of_constrained_len/')
    def test_render_default(self):
        self.assertTrue('At Least 2' in browser.page_source)
        self.assertEqual(findid('deformField1-addtext').text, 'Add Name')
        self.assertEqual(findid('captured').text, 'None')
        # default 2 inputs rendered
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('deformField4').get_attribute('value'), '')

    def test_add_and_remove(self):
        self.assertEqual(findid('deformField1-addtext').text, 'Add Name')
        findid('deformField3').send_keys('hello1')
        findid('deformField4').send_keys('hello2')
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[2].send_keys('hello3')
        findxpaths('//input[@name="name"]')[3].send_keys('hello4')

        self.assertFalse(findid("deformField1-seqAdd").is_displayed())
        findid("deformField3-close").click()
        self.assertTrue(findid("deformField1-seqAdd").is_displayed())
        findid("deformField1-seqAdd").click()
        self.assertFalse(findid("deformField1-seqAdd").is_displayed())
        findxpaths('//input[@name="name"]')[3].send_keys('hello5')
        findid("deformsubmit").click()
        self.assertFalse(findid("deformField1-seqAdd").is_displayed())
        self.assertEqual(
            eval(findid('captured').text),
            {'names': [u'hello2', u'hello3', u'hello4', u'hello5']}
            )

class SequenceOfRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_richtext/")
    def test_render_default(self):
        self.assertTrue('Texts' in browser.page_source)
        self.assertEqual(findid('deformField1-addtext').text, 'Add Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('deformField1-addtext').text, 'Add Text')
        self.assertEqual(findid('captured').text, "{'texts': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_filled(self):
        findid("deformField1-seqAdd").click()
        browser.switch_to_frame(browser.find_element_by_tag_name('iframe'))
        findid('tinymce').send_keys('yo')
        browser.switch_to_default_content()
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'texts': [u'<p>yo</p>']})

class SequenceOfMaskedTextInputs(Base, unittest.TestCase):
    url = test_url("/sequence_of_masked_textinputs/")
    def test_render_default(self):
        self.assertTrue('Texts' in browser.page_source)
        self.assertEqual(findid('deformField1-addtext').text,'Add Text')
        self.assertEqual(findid('captured').text, 'None')
        
    def test_submit_none_added(self):
        findid('deformsubmit').click()
        self.assertEqual(findid('deformField1-addtext').text,'Add Text')
        self.assertEqual(findid('captured').text, "{'texts': []}")
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_two_unfilled(self):
        findid('deformField1-seqAdd').click()
        findid('deformField1-seqAdd').click()
        findid('deformsubmit').click()
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_filled(self):
        browser.get(self.url)
        findid('deformField1-seqAdd').click()
        textbox = findxpaths('//input[@name="text"]')[0]
        textbox.click()
        textbox.send_keys('140118866')
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        captured = findid('captured').text
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
        self.assertTrue('Pepper' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'pepper')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'- Select -', u'Habanero', u'Jalapeno', u'Chipotle']) 
        self.assertEqual(findcss('.required').text, 'Pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_default(self):
        findid('deformsubmit').click()
        self.assertTrue('Pepper' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'pepper')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        self.assertTrue(
            findid('captured').text in self.submit_selected_captured
            )

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
        select = findid('deformField1')
        self.assertTrue(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        options[0].click()
        options[2].click()

        findid('deformsubmit').click()

        captured_default = {'pepper': set([u'chipotle', u'habanero'])}
        self.assertEqual(eval(findid('captured').text), captured_default)
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

class SelectWidgetIntegerTests(Base, unittest.TestCase):
    url = test_url('/select_integer/')
    def test_render_default(self):
        self.assertTrue('Number' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'number')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'- Select -', u'Zero', u'One', u'Two']
            )
        self.assertEqual(findcss('.required').text, 'Number')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_default(self):
        findid('deformsubmit').click()
        self.assertTrue('Number' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'number')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured, 
            "{'number': 0}")
        
class SelectWidgetWithOptgroupTests(Base, unittest.TestCase):
    url = test_url("/select_with_optgroup/")

    def test_render_default(self):
        self.assertTrue('Musician' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'musician')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'Select your favorite musician',
             u'Jimmy Page', u'Jimi Hendrix', u'Billy Cobham', u'John Bonham']
            )
        self.assertEqual(findcss('.required').text, 'Musician')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(len(findxpaths('//optgroup')), 2)
        
    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            "{'musician': 'page'}",
            )

class SelectWidgetWithOptgroupAndLabelTests(SelectWidgetWithOptgroupTests):
    url = test_url("/select_with_optgroup_and_label_attributes/")

    def test_render_default(self):
        self.assertTrue('Musician' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'musician')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'Select your favorite musician',
             u'Guitarists - Jimmy Page',
             u'Guitarists - Jimi Hendrix',
             u'Drummers - Billy Cobham',
             u'Drummers - John Bonham']
            )
        self.assertEqual(findcss('.required').text, 'Musician')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(len(findxpaths('//optgroup')), 2)
        
    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            "{'musician': 'page'}",
            )

class SelectReadonlyTests(Base, unittest.TestCase):
    url = test_url("/select_readonly/")

    def test_render_default(self):
        musician = findid('deformField1-2-0')
        self.assertEqual(musician.text, 'Billy Cobham')
        multi1 = findid('deformField2-1-0')
        self.assertEqual(multi1.text, 'Jimmy Page')
        multi2 = findid('deformField2-2-0')
        self.assertEqual(multi2.text, 'Billy Cobham')
        self.assertEqual(findid('captured').text, 'None')

class Select2WidgetTests(Base, unittest.TestCase):
    url = test_url("/select2/")
    submit_selected_captured = (
        "{'pepper': u'habanero'}",
        "{'pepper': 'habanero'}",
        )

    def test_render_default(self):
        self.assertTrue('Pepper' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'pepper')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'- Select -', u'Habanero', u'Jalapeno', u'Chipotle']) 
        self.assertEqual(findcss('.required').text, 'Pepper')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_default(self):
        findid('deformsubmit').click()
        self.assertTrue('Pepper' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'pepper')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        self.assertTrue(
            findid('captured').text in self.submit_selected_captured
            )

class Select2WidgetMultipleTests(Base, unittest.TestCase):
    url = test_url('/select2_with_multiple/')

    def test_submit_selected(self):
        select = findid('deformField1')
        self.assertTrue(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        options[0].click()
        options[2].click()

        findid('deformsubmit').click()

        captured_default = {'pepper': set([u'chipotle', u'habanero'])}
        self.assertEqual(eval(findid('captured').text), captured_default)
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

class Select2WidgetWithOptgroupTests(Base, unittest.TestCase):
    url = test_url("/select2_with_optgroup/")

    def test_render_default(self):
        self.assertTrue('Musician' in browser.page_source)
        select = findid('deformField1')
        self.assertEqual(select.get_attribute('name'), 'musician')
        self.assertFalse(select.get_attribute('multiple'))
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [u'Select your favorite musician',
             u'Jimmy Page', u'Jimi Hendrix', u'Billy Cobham', u'John Bonham']
            )
        self.assertEqual(findcss('.required').text, 'Musician')
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(len(findxpaths('//optgroup')), 2)
        
    def test_submit_selected(self):
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        options[1].click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        select = findid('deformField1')
        options = select.find_elements_by_tag_name('option')
        self.assertTrue(options[1].is_selected())
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured,
            "{'musician': 'page'}",
            )


class TextInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput/")
    def test_render_default(self):
        self.assertTrue('Text' in browser.page_source)
        element = findid('deformField1')
        self.assertEqual(element.get_attribute('name'), 'text')
        self.assertEqual(element.get_attribute('type'), 'text')
        self.assertEqual(element.get_attribute('value'), '')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformsubmit').click()
        element = findid('deformField1')
        self.assertEqual(element.get_attribute('name'), 'text')
        self.assertEqual(element.get_attribute('type'), 'text')
        self.assertEqual(element.get_attribute('value'), '')
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_filled(self):
        findid('deformField1').send_keys('hello')
        findid('deformsubmit').click()
        element = findid('deformField1')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(element.get_attribute('value'), 'hello')
        captured = findid('captured').text
        self.assertSimilarRepr(
            captured, 
            "{'text': u'hello'}")

class TextInputWithCssClassWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput_with_css_class/")
    def test_render_default(self):
        findcss('.deformWidgetWithStyle')
        
class MoneyInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/money_input/")
    def test_render_default(self):
        findid('deformField1').send_keys('')
        self.assertTrue('Greenbacks' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'greenbacks')
        self.assertEqual(findid('deformField1').get_attribute('type'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '0.00')
        self.assertEqual(findcss('.required').text, 'Greenbacks')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformField1').send_keys('')
        findid('deformsubmit').click()
        self.assertEqual(findid('captured').text,
                         "{'greenbacks': Decimal('0.00')}")

    def test_submit_filled(self):
        findid('deformField1').send_keys(5 * Keys.ARROW_LEFT)
        findid('deformField1').send_keys('10')
        findid('deformsubmit').click()
        self.assertEqual(findid('captured').text,
                         "{'greenbacks': Decimal('100.00')}")
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

class AutocompleteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_input/")
    def test_render_default(self):
        self.assertTrue('Autocomplete Input Widget' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('type'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformsubmit').click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_filled(self):
        findid('deformField1').send_keys('ba')
        self.assertTrue(findxpath('//p[text()="baz"]').is_displayed())
        findid('deformField1').send_keys('r')
        findcss('.tt-suggestion').click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text,
                         "{'text': u'bar'}")

class AutocompleteRemoteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_remote_input/")
    def test_render_default(self):
        self.assertTrue('Autocomplete Input Widget (with Remote Data Source)'
                        in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('type'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformsubmit').click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_filled(self):
        findid('deformField1').send_keys('t')
        time.sleep(0.5)
        self.assertTrue(findxpath('//p[text()="two"]').is_displayed())
        self.assertTrue(findxpath('//p[text()="three"]').is_displayed())
        findcss('.tt-suggestion').click()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text,
                         "{'text': u'two'}")

class TextAreaWidgetTests(Base, unittest.TestCase):
    url = test_url("/textarea/")
    def test_render_default(self):
        self.assertTrue('Text' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('rows'),
                         '10')
        self.assertEqual(findid('deformField1').get_attribute('cols'),
                         '60')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformsubmit').click()
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertTrue(findcss('.has-error'))

    def test_submit_filled(self):
        findid('deformField1').send_keys('hello')
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('captured').text,
                         "{'text': u'hello'}")

class TextAreaReadonlyTests(Base, unittest.TestCase):
    url = test_url("/textarea_readonly/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1').text,
                         'text')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

        
class DelayedRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/delayed_richtext/")
    def test_submit_filled(self):
        findcss('.tinymce-preload').click()
        time.sleep(0.5)
        browser.switch_to_frame(browser.find_element_by_tag_name('iframe'))
        findid('tinymce').send_keys('hello')
        browser.switch_to_default_content()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(eval(findid('captured').text),
                         {'text': u'<p>hello</p>'})

class RichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/richtext/")
    def test_render_default(self):
        self.assertTrue('Text' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'text')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_empty(self):
        findid('deformsubmit').click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertTrue(findcss('.has-error'))
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_filled(self):
        browser.switch_to_frame(browser.find_element_by_tag_name('iframe'))
        findid('tinymce').send_keys('hello')
        browser.switch_to_default_content()
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(eval(findid('captured').text),
                         {'text': u'<p>hello</p>'})

class RichTextWidgetInternationalized(Base, unittest.TestCase):
    url = test_url("/richtext_i18n/?_LOCALE_=ru")
    def test_render_default(self):
        self.assertTrue('Text' in browser.page_source)
        self.assertTrue(u"Формат" in browser.page_source)

class RichTextReadonlyTests(Base, unittest.TestCase):
    url = test_url("/richtext_readonly/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1').text, '<p>Hi!</p>')
        self.assertEqual(findcss('.required').text, 'Text')
        self.assertEqual(findid('captured').text, 'None')

class UnicodeEverywhereTests(Base, unittest.TestCase):
    url = test_url("/unicodeeverywhere/")
    def test_render_default(self):
        description=(u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？ "
                     u"人不知而不慍，不亦君子乎？」")

        self.assertTrue(u"По оживлённым берегам" in browser.page_source)
        self.assertEqual(findcss('.help-block').text,
                         description)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'field')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         u'☃')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit(self):
        findid('deformsubmit').click()
        self.assertRaises(NoSuchElementException, findcss, '.has-error')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         u'☃')
        captured = findid('captured').text
        self.assertTrue(
            captured in (
                u"{'field': u'\\u2603'}", # py2
                u"{'field': '\u2603'}",  # py3
            )
            )

class SequenceOfSequencesTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_sequences/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1-addtext').text,
                         'Add Names and Titles')
        self.assertEqual(findid('deformField6-addtext').text,
                         'Add Name and Title')
        self.assertEqual(findid('deformField21').text, '')
        self.assertEqual(findid('deformField22').text, '')
        self.assertEqual(findid('captured').text, 'None')

    def test_add_two(self):
        findid("deformField1-seqAdd").click()
        findid("deformField6-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].send_keys('name')
        findxpaths('//input[@name="title"]')[0].send_keys('title')
        findxpaths('//input[@name="name"]')[1].send_keys('name')
        findxpaths('//input[@name="title"]')[1].send_keys('title')
        findxpaths('//input[@name="name"]')[2].send_keys('name')
        findxpaths('//input[@name="title"]')[2].send_keys('title')
        findid('deformsubmit').click()
        self.assertEqual(eval(findid('captured').text),
                         {'names_and_titles_sequence': [
                             [{'name': u'name', 'title': u'title'},
                              {'name': u'name', 'title': u'title'}],
                             [{'name': u'name', 'title': u'title'}]]})

    def test_remove_from_nested_mapping_sequence(self):
        findid("deformField1-seqAdd").click()
        self.assertEqual(len(findxpaths('//input[@name="name"]')), 2)
        findcsses('.deformClosebutton')[3].click()
        self.assertEqual(len(findxpaths('//input[@name="name"]')), 1)

class SequenceOrderableTests(Base, unittest.TestCase):
    url = test_url("/sequence_orderable/")
    def test_render_default(self):
        self.assertTrue(findcss('.deformProto'))
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1-addtext').text,
                         'Add Person')

    def test_submit_complex_interaction(self):
        findid("deformField1-seqAdd").click()

        # A single item shouldn't have an active reorder button.
        self.assertEqual(len(findcsses('.deformOrderbutton')), 1)
        self.assertFalse(findcsses('.deformOrderbutton')[0].is_displayed())
        
        # add a second
        findid("deformField1-seqAdd").click()
        # Now there should be 2 active reorder buttons.
        self.assertEqual(len(findcsses('.deformOrderbutton')), 2)
        self.assertTrue(findcsses('.deformOrderbutton')[0].is_displayed())
        self.assertTrue(findcsses('.deformOrderbutton')[1].is_displayed())

        # add a third
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].send_keys('Name1')
        findxpaths('//input[@name="age"]')[0].send_keys('11')
        findxpaths('//input[@name="name"]')[1].send_keys('Name2')
        findxpaths('//input[@name="age"]')[1].send_keys('22')
        findxpaths('//input[@name="name"]')[2].send_keys('Name3')
        findxpaths('//input[@name="age"]')[2].send_keys('33')

        order1_id = findcsses('.deformOrderbutton')[0].get_attribute('id')
        order3_id = findcsses('.deformOrderbutton')[2].get_attribute('id')
        seq_height = findcss('.deformSeqItem').size['height']

        # Move item 3 up two
        actions = ActionChains(browser)
        actions.drag_and_drop_by_offset(
            findid(order3_id), 0, -seq_height * 2.5).perform()

        # Move item 1 down one slot (actually a little more than 1 is
        # needed to trigger jQuery Sortable when dragging down, so use 1.5).
        actions = ActionChains(browser)
        actions.drag_and_drop_by_offset(
            findid(order1_id), 0, seq_height * 1.5).perform()

        findid('deformsubmit').click()

        # sequences should be in reversed order
        inputs = findxpaths('//input[@name="name"]')
        self.assertEqual(inputs[0].get_attribute('value'), 'Name3')
        self.assertEqual(inputs[1].get_attribute('value'), 'Name2')
        self.assertEqual(inputs[2].get_attribute('value'), 'Name1')

        self.assertEqual(eval(findid('captured').text),
                         {'people': [
                         {'name': 'Name3', 'age': 33},
                         {'name': 'Name2', 'age': 22},
                         {'name': 'Name1', 'age': 11},
                     ]})

class TextAreaCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textareacsv/")
    def test_render_default(self):
        self.assertTrue('Csv' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'csv')
        self.assertEqual(findid('deformField1').get_attribute('rows'),
                         '10')
        self.assertEqual(findid('deformField1').get_attribute('cols'),
                         '60')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '1,hello,4.5\n2,goodbye,5.5\n')
        self.assertEqual(findcss('.required').text, 'Csv')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_default(self):
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'csv': [(1, u'hello', Decimal("4.5")), 
                                  (2, u'goodbye', Decimal("5.5"))]
                         })

    def test_submit_line_error(self):
        findid('deformField1').clear()
        findid('deformField1').send_keys('1,2,3\nwrong')
        findid("deformsubmit").click()
        self.assertEqual(findid('captured').text, 'None')
        self.assertTrue(
            'has an incorrect number of elements (expected 3, was 1)' in
            findid('error-deformField1').text
            )

    def test_submit_empty(self):
        findid('deformField1').clear()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

class WidgetAdapterTests(TextAreaCSVWidgetTests):
    url = test_url("/widget_adapter/")

class TextInputCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinputcsv/")
    def test_render_default(self):
        self.assertTrue('Csv' in browser.page_source)
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '1,hello,4.5')
        self.assertEqual(findcss('.required').text, 'Csv')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_default(self):
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'csv': (1, u'hello', Decimal("4.5"))})

    def test_submit_line_error(self):
        findid('deformField1').clear()
        findid('deformField1').send_keys('1,2,wrong')
        findid("deformsubmit").click()
        self.assertEqual(findid('captured').text, 'None')
        self.assertTrue(
            '"wrong" is not a number' in findid('error-deformField1').text
            )

    def test_submit_empty(self):
        findid('deformField1').clear()
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

class MultipleFormsTests(Base, unittest.TestCase):
    url = test_url("/multiple_forms/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1').get_attribute('name'),
                         'name1')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '')
        self.assertEqual(findid('deformField3').get_attribute('name'),
                         'name2')
        self.assertEqual(findid('deformField3').get_attribute('value'),
                         '')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_first(self):
        findid('deformField1').send_keys('hey')
        findid("form1submit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'name1': 'hey'})

    def test_submit_second(self):
        findid('deformField3').send_keys('hey')
        findid("form2submit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'name2': 'hey'})

class RequireOneFieldOrAnotherTests(Base, unittest.TestCase):
    url = test_url("/require_one_or_another/")
    def test_render_default(self):
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField1').get_attribute('name'), 'one')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('name'), 'two')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_submit_none_filled(self):
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text,
                         'Required if two is not supplied')
        self.assertEqual(findid('error-deformField2').text,
                         'Required if one is not supplied')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_one_filled(self):
        findid("deformField1").send_keys('one')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                         {'one': u'one', 'two': u''})
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

class AjaxFormTests(Base, unittest.TestCase):
    url = test_url("/ajaxform/")
    def test_render_default(self):
        self.assertEqual(findid('captured').text, 'None')
        self.assertEqual(findid('deformField1').get_attribute('value'), '')
        self.assertEqual(findid('deformField3').get_attribute('value'), '')
        self.assertEqual(findid('deformField4').get_attribute('value'), '')
        self.assertEqual(
            findid('deformField4-month').get_attribute('value'), '')
        self.assertEqual(findid('deformField4-day').get_attribute('value'), '')

    def test_submit_empty(self):
        source = browser.page_source
        findid("deformsubmit").click()
        wait_for_ajax(source)
        self.assertEqual(findid('error-deformField1').text, 'Required')
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_invalid(self):
        findid('deformField1').send_keys('notanumber')
        source = browser.page_source
        findid("deformsubmit").click()
        wait_for_ajax(source)
        self.assertEqual(findid('error-deformField1').text,
                         '"notanumber" is not a number')
        self.assertEqual(findid('error-deformField3').text, 'Required')
        self.assertEqual(findid('error-deformField4').text, 'Required')
        self.assertEqual(findid('captured').text, 'None')

    def test_submit_success(self):
        findid('deformField1').send_keys('1')
        findid('deformField3').send_keys('name')
        findid('deformField4').send_keys('2010')
        findid('deformField4-month').send_keys('1')
        findid('deformField4-day').send_keys('1')
        browser.switch_to_frame(browser.find_element_by_tag_name('iframe'))
        findid('tinymce').send_keys('yo')
        browser.switch_to_default_content()
        source = browser.page_source
        findid("deformsubmit").click()
        wait_for_ajax(source)
        self.assertEquals(findid('thanks').text, 'Thanks!')

class RedirectingAjaxFormTests(AjaxFormTests):
    url = test_url("/ajaxform_redirect/")
    def test_submit_success(self):
        findid('deformField1').send_keys('1')
        findid('deformField3').send_keys('name')
        findid('deformField4').send_keys('2010')
        findid('deformField4-month').send_keys('1')
        findid('deformField4-day').send_keys('1')
        source = browser.page_source
        findid("deformsubmit").click()
        wait_for_ajax(source)
        self.assertTrue(browser.current_url.endswith('thanks.html'))

class TextInputMaskTests(Base, unittest.TestCase):
    url = test_url("/text_input_masks/")
    def test_render_default(self):
        findid('deformField1').send_keys('')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '___-__-____')
        self.assertEqual(findid('deformField1').get_attribute('name'), 'ssn')
        self.assertEqual(findid('deformField2').get_attribute('value'), '')
        self.assertEqual(findid('deformField2').get_attribute('name'), 'date')
        self.assertRaises(NoSuchElementException, findcss, '.has-error')

    def test_type_bad_input(self):
        findid('deformField1').send_keys('')
        findid('deformField1').send_keys('a')
        self.assertEqual(findid('deformField1').get_attribute('value'),
                         '___-__-____')
        findid('deformField2').send_keys('')
        findid('deformField2').send_keys('a')

        self.assertEqual(findid('deformField2').get_attribute('value'),
                         '__/__/____')

    def test_submit_success(self):
        findid('deformField1').send_keys('')
        findid('deformField1').send_keys('140118866')
        browser.execute_script(
            'document.getElementById("deformField2").focus();')
        findid('deformField2').send_keys('10102010')
        findid("deformsubmit").click()
        self.assertEqual(eval(findid('captured').text),
                        {'date': u'10/10/2010', 'ssn': u'140-11-8866'})

class MultipleErrorMessagesInMappingTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_mapping/")
    def test_it(self):
        findid('deformField1').send_keys('whatever')
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField1').text, 'Error 1')
        self.assertEqual(findid('error-deformField1-1').text, 'Error 2')
        self.assertEqual(findid('error-deformField1-2').text, 'Error 3')

class MultipleErrorMessagesInSequenceTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_seq/")
    def test_it(self):
        findid("deformField1-seqAdd").click()
        findxpath("//input[@name='field']").send_keys('whatever')
        findid("deformsubmit").click()
        self.assertEqual(findid('error-deformField3').text, 'Error 1')
        self.assertEqual(findid('error-deformField3-1').text, 'Error 2')
        self.assertEqual(findid('error-deformField3-2').text, 'Error 3')

class CssClassesOnTheOutermostHTMLElementTests(Base, unittest.TestCase):
    url = test_url("/custom_classes_on_outermost_html_element/")
    def test_it(self):
        findcss('form > fieldset > div.top_level_mapping_widget_custom_class')
        findcss('[title=MappingWidget] div.mapped_widget_custom_class')
        findcss('[title=SequenceWidget] div.sequenced_widget_custom_class')
        

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()

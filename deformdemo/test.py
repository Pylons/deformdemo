# -*- coding: utf-8 -*-
# Standard Library
from __future__ import print_function

import ast
import datetime
from decimal import Decimal
import logging
import os
import re
import sys
import time
import unittest

# Test Support
from flaky import flaky
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


browser = None

#: Where we write stuff when Selenium doesn't work
BROKEN_SELENIUM_LOG_FILE = "/tmp/selenium.log"

# Some sleep we assume the datetime widget takes to show or hide
# itself properly
DATE_PICKER_DELAY = 1.0

BASE_PATH = os.environ.get("BASE_PATH", "")
URL = os.environ.get("URL", "http://localhost:8522")
PY3 = sys.version_info[0] == 3

#: Wait 2.0 seconds for some Selenium events to happen before giving up
SELENIUM_IMPLICIT_WAIT = 1.0


# Disable unnecessary Selenium trace output bloat
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(
    logging.WARN
)


def give_selenium_some_time(func):
    """Function decorator to give Selenium finds implicit timeout.

    For example, when rendering datetime widgets, the page layout
    is not final until JavaScript mutates DOM tree.

    This yields to false errors like:

    Message: unknown error: Element is not clickable at point (1016, 178).
    Other element would receive the click:
        <div class="picker__holder" tabindex="-1" style="">...</div>
    """

    def inner(*args, **kwargs):

        deadline = time.time() + SELENIUM_IMPLICIT_WAIT
        sleep = 0.03

        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, NoSuchElementException):
                    # Retryable Selenium exception
                    if time.time() >= deadline:
                        raise
                else:
                    raise

            time.sleep(sleep)
            sleep *= 2

    return inner


def action_chains_on_id(eid):
    return ActionChains(browser).move_to_element(
        WebDriverWait(browser, SELENIUM_IMPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, eid))
        )
    )


def action_chains_on_xpath(expath):
    return ActionChains(browser).move_to_element(
        WebDriverWait(browser, SELENIUM_IMPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.XPATH, expath))
        )
    )


def action_chains_xpath_on_select(option_xpath):
    return ActionChains(browser).move_to_element(
        browser.find_element_by_xpath(option_xpath)
    )


def action_chains_on_css_selector(css_selector):
    return ActionChains(browser).move_to_element(findcss(css_selector))


@give_selenium_some_time
def findid(elid, clickable=True):
    """Find Selenium element by CSS id.

    :param clickable: Make sure element has become clickable before returning.
    """

    if clickable:
        # http://stackoverflow.com/a/26943922/315168
        element = WebDriverWait(browser, SELENIUM_IMPLICIT_WAIT).until(
            EC.element_to_be_clickable((By.ID, elid))
        )
        return element
    else:
        return browser.find_element_by_id(elid)


def findid_view(elid):
    """Find an element and hope its there in the some point of time."""
    deadline = time.time() + SELENIUM_IMPLICIT_WAIT

    while True:
        try:
            return browser.find_element_by_id(elid)
        except NoSuchElementException:
            if time.time() < deadline:
                # FLAKY is fun!
                time.sleep(0.02)
                continue

            raise


@give_selenium_some_time
def findcss(selector):
    return browser.find_element_by_css_selector(selector)


@give_selenium_some_time
def findcsses(selector):
    return browser.find_elements_by_css_selector(selector)


@give_selenium_some_time
def findxpath(selector):
    return browser.find_element_by_xpath(selector)


@give_selenium_some_time
def findxpaths(selector):
    return browser.find_elements_by_xpath(selector)


def wait_for_ajax(source):
    def compare_source(driver):
        try:
            return source != driver.page_source
        except WebDriverException:
            pass

    WebDriverWait(browser, 5).until(compare_source)


def wait_until_visible(selector, max_wait=5.0):
    """Wait until something is visible.

    """
    # http://stackoverflow.com/a/13058101/315168
    element = WebDriverWait(browser, max_wait).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    return element


def wait_to_click(selector):
    """Try to click element and wait if something is obscuring the cursor."""
    deadline = time.time() + SELENIUM_IMPLICIT_WAIT
    while time.time() < deadline:
        try:
            elems = browser.find_elements_by_css_selector(selector)
            # assert len(elems) == 1, "Got {} for {}".format(elems, selector)
            if len(elems) > 0:
                elems[0].click()
                return
            else:
                # Haha what a gotcha!
                time.sleep(0.2)
        except Exception as e:

            if isinstance(e, StaleElementReferenceException):
                # Look all these exceptions we can get!
                time.sleep(0.2)
                continue

            if isinstance(e, WebDriverException):
                if "not clickable" in e.msg:
                    # SO FUN!
                    time.sleep(0.2)
                    continue
            raise


def pick_today():
    """Pick a today in datetime picker."""
    wait_until_visible(".picker__button--today")
    findcss(".picker__button--today").click()
    time.sleep(1)


def wait_picker_to_show_up():
    # TODO: This tests uses explicit waits to make it run on a modern browsers.
    # The waits could be replaced by calling picker JS API directly
    # inside Selenium browser
    # TODO: This is caused by animation. Disable animations for tests.
    time.sleep(1.0)


def submit_date_picker_safe():
    """Delays caused by animation."""
    wait_to_click("#deformsubmit")


def sort_set_values(captured):
    """
    Sets have no sort order in Python 3, but strangely they do in Python 2???

    Whatever.  When we drop Python 2, we don't have to do this nonsense and can
    simply compare two sets with ast.

    :param captured:
    :type captured:
    :return:
    :rtype:
    """
    obj = ast.literal_eval(captured)
    for _k, _v in obj.items():
        pass
    vs = sorted(_v)
    return "{'" + _k + "': {'" + ("', '").join(vs) + "'}}"


def setUpModule():

    global browser

    # Quick override for testing with different browsers
    driver_name = os.environ.get("WEBDRIVER")

    if driver_name == "chrome":
        # Test Support
        from selenium.webdriver import Chrome

        browser = Chrome()
        return browser
    elif driver_name == "phantomjs":
        # TODO: Test fails on Phantomjs
        # They just hang in some point
        # Test Support
        from selenium.webdriver import PhantomJS

        browser = PhantomJS()
    else:
        # Test Support
        from selenium.webdriver import Firefox
        from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

        firefox_path = os.environ.get("FIREFOX_PATH")

        binary = FirefoxBinary(
            firefox_path=firefox_path,
            log_file=open(BROKEN_SELENIUM_LOG_FILE, "wt"),
        )
        try:
            browser = Firefox(firefox_binary=binary)
            browser.set_window_size(1920, 1080)
        except WebDriverException:
            if os.path.exists(BROKEN_SELENIUM_LOG_FILE):
                print("Selenium says no")
                print(open(BROKEN_SELENIUM_LOG_FILE, "rt").read())
            raise
        return browser


def tearDownModule():
    browser.quit()


def _getFile(name="test.py"):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    filename = os.path.split(path)[-1]
    return path, filename


# appease nosetests by giving a default argument, it thinks this is a test
def test_url(url=""):
    return URL + BASE_PATH + url


class Base(object):
    urepl = re.compile("\\bu('.*?'|\".*?\")")  # noQA
    setrepl = re.compile("set\(\[(.*)\]\)")  # noQA

    def setUp(self):
        browser.get(self.url)

    def tearDown(self):
        # it should never happen that classes include None keyword
        # (poor mans html parser):
        for class_ in re.finditer(r'class="([^"]*)"', browser.page_source):
            self.assertFalse("None" in class_.group(1))
        for class_ in re.finditer(r"class='([^']*)'", browser.page_source):
            self.assertFalse("None" in class_.group(1))

    def assertSimilarRepr(self, a, b):
        # ignore u'' and and \n in reprs, normalize set syntax between py2 and
        # py3
        ar = a.replace("\n", "")
        ar = self.urepl.sub(r"\1", ar)
        ar = self.setrepl.sub(r"{\1}", ar)
        br = b.replace("\n", "")
        br = self.urepl.sub(r"\1", br)
        br = self.setrepl.sub(r"{\1}", br)
        self.assertEqual(ar.replace(" ", ""), br.replace(" ", ""))


class CheckboxChoiceWidgetTests(Base, unittest.TestCase):

    url = test_url("/checkboxchoice/")

    def test_render_default(self):
        self.assertTrue("Pepper" in browser.page_source)
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findcss(".required").text, "Pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_unchecked(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        error_node = "error-deformField1"
        self.assertEqual(
            findid(error_node).text, "Shorter than minimum length 1"
        )
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(findid("deformField1-0").is_selected())
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'pepper': {'habanero'}}")

    def test_submit_three_checked(self):
        findid("deformField1-0").click()
        findid("deformField1-1").click()
        findid("deformField1-2").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(findid("deformField1-0").is_selected())
        self.assertTrue(findid("deformField1-1").is_selected())
        self.assertTrue(findid("deformField1-2").is_selected())
        captured = findid("captured").text
        if PY3:
            captured = sort_set_values(captured)
        expected = "{'pepper': {'chipotle', 'habanero', 'jalapeno'}}"
        self.assertSimilarRepr(captured, expected)


class CheckboxChoiceWidgetInlineTests(Base, unittest.TestCase):
    url = test_url("/checkboxchoice_inline/")

    def test_render_default(self):
        self.assertTrue("Pepper" in browser.page_source)
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findcss(".required").text, "Pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_unchecked(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        error_node = "error-deformField1"
        self.assertEqual(
            findid(error_node).text, "Shorter than minimum length 1"
        )
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(findid("deformField1-0").is_selected())
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'pepper': {'habanero'}}")

    def test_submit_three_checked(self):
        findid("deformField1-0").click()
        findid("deformField1-1").click()
        findid("deformField1-2").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(findid("deformField1-0").is_selected())
        self.assertTrue(findid("deformField1-1").is_selected())
        self.assertTrue(findid("deformField1-2").is_selected())
        captured = findid("captured").text
        if PY3:
            captured = sort_set_values(captured)
        expected = "{'pepper': {'chipotle', 'habanero', 'jalapeno'}}"
        self.assertSimilarRepr(captured, expected)


class CheckboxChoiceReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkboxchoice_readonly/")

    def test_render_default(self):
        self.assertTrue("Pepper" in browser.page_source)
        self.assertEqual(findid("deformField1-1").text, "Jalapeno")
        self.assertEqual(findid("deformField1-2").text, "Chipotle")
        self.assertEqual(findid("captured").text, "None")


class CheckboxWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkbox/")

    def test_render_default(self):
        self.assertTrue("I Want It!" in browser.page_source)
        self.assertFalse(findid("deformField1").is_selected())
        self.assertEqual(findcss(".required").text, "I Want It!")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_unchecked(self):
        wait_to_click("#deformsubmit")
        self.assertFalse(findid_view("deformField1").is_selected())
        self.assertEqual(findid_view("captured").text, "{'want': False}")

    def test_submit_checked(self):
        findid("deformField1").click()
        wait_to_click("#deformsubmit")
        self.assertTrue(findid_view("deformField1").is_selected())
        self.assertEqual(findid_view("captured").text, "{'want': True}")


class CheckboxReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkbox_readonly/")

    def test_render_default(self):
        self.assertTrue("I Want It!" in browser.page_source)
        self.assertEqual(findid("deformField1").text, "True")
        self.assertEqual(findid("captured").text, "None")


class CheckedInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedinput/")

    def test_render_default(self):
        self.assertTrue("Email Address" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Email Address")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_invalid(self):
        findid("deformField1").send_keys("this")
        findid("deformField1-confirm").send_keys("this")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text, "Invalid email address"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "this"
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), "this"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_mismatch(self):
        findid("deformField1").send_keys("this@example.com")
        findid("deformField1-confirm").send_keys("that@example.com")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text, "Fields did not match"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"),
            "this@example.com",
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"),
            "that@example.com",
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField1").send_keys("user@example.com")
        findid("deformField1-confirm").send_keys("user@example.com")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"),
            "user@example.com",
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"),
            "user@example.com",
        )
        self.assertTrue("user@example.com" in findid("captured").text)


@flaky
class CheckedInputWidgetWithMaskTests(Base, unittest.TestCase):
    url = test_url("/checkedinput_withmask/")

    def test_render_default(self):
        self.assertEqual(findcss(".required").text, "Social Security Number")
        self.assertEqual(findid("captured").text, "None")

        # Ensure the masked input has a focus and ### mask
        # has kicked in
        action_chains_on_id("deformField1").send_keys("0").perform()

        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "0##-##-####"
        )

        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_type_bad_input(self):
        action_chains_on_id("deformField1").send_keys("a").perform()
        action_chains_on_id("deformField1-confirm").send_keys("a").perform()
        self.assertTrue(
            findid_view("deformField1").get_attribute("value")
            in ("", "###-##-####")
        )
        self.assertTrue(
            findid("deformField1-confirm").get_attribute("value")
            in ("", "###-##-####")
        )

        action_chains_on_id("deformField1").send_keys("140118866").perform()

        browser.execute_script(
            'document.getElementById("deformField1-confirm").focus();'
        )

        action_chains_on_id("deformField1-confirm").send_keys(
            "140118866"
        ).perform()

        wait_to_click("#deformsubmit")
        time.sleep(1)  # SUPER FLAKY
        text = findid_view("captured").text
        self.assertTrue("140-11-8866" in text, "Got {}".format(text))


class CheckedInputReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkedinput_readonly/")

    def test_render_default(self):
        self.assertTrue("Email Address" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Email Address")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(findid("deformField1").text, "ww@graymatter.com")


class CheckedPasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword/")

    def test_submit_tooshort(self):
        findid("deformField1").send_keys("this")
        findid("deformField1-confirm").send_keys("this")
        findcss("#deformsubmit").click()
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text, "Shorter than minimum length 5"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid_view("deformField1-confirm").get_attribute("value"), ""
        )

    def test_submit_mismatch(self):
        findid("deformField1").send_keys("this123")
        findid("deformField1-confirm").send_keys("that123")
        findcss("#deformsubmit").click()

        self.assertEqual(
            findid_view("error-deformField1").text,
            "Password did not match confirm",
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        wait_until_visible("#deformField1")
        findid("deformField1").send_keys("this123")
        findid("deformField1-confirm").send_keys("this123")
        findcss("#deformsubmit").click()

        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertEqual(
            findid_view("captured").text, "{'password': 'this123'}"
        )


class CheckedPasswordRedisplayWidgetTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword_redisplay/")

    def test_render_default(self):
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Password")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("type"), "password"
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("type"), "password"
        )

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), ""
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_tooshort(self):
        findid("deformField1").send_keys("this")
        findid("deformField1-confirm").send_keys("this")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text, "Shorter than minimum length 5"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "this"
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), "this"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_mismatch(self):
        findid("deformField1").send_keys("this123")
        findid("deformField1-confirm").send_keys("that123")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid("error-deformField1").text, "Password did not match confirm"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "this123"
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), "that123"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField1").send_keys("this123")
        findid("deformField1-confirm").send_keys("this123")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "this123"
        )
        self.assertEqual(
            findid("deformField1-confirm").get_attribute("value"), "this123"
        )
        self.assertTrue("this123" in findid("captured").text)


class CheckedPasswordReadonlyTests(Base, unittest.TestCase):
    url = test_url("/checkedpassword_readonly/")

    def test_render_default(self):
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Password")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid("deformField1").text, "Password not displayed."
        )


@flaky
class DateInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/dateinput/")

    def test_render_default(self):
        self.assertTrue("Date" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Date")
        self.assertEqual(findid_view("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid_view("error-deformField1").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid_view("captured").text, "None")

    def test_submit_tooearly(self):
        findid("deformField1").click()
        wait_picker_to_show_up()

        def diff_month(d1, d2):
            return (d1.year - d2.year) * 12 + d1.month - d2.month + 1

        tooearly = datetime.date(datetime.date.today().year, 1, 1)
        today = datetime.date.today()
        num_months = diff_month(today, tooearly)
        time.sleep(DATE_PICKER_DELAY)
        for _x in range(num_months):
            findcss(".picker__nav--prev").click()
            # Freaking manual timing here again
            time.sleep(0.2)

        time.sleep(0.5)
        wait_to_click(".picker__day")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertTrue("is earlier than" in findid("error-deformField1").text)
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        # TODO: This tests uses explicit waits to run on modern browsers.
        # The waits could be replaced by calling picker JS API directly
        # inside Selenium browser
        today = datetime.date.today()
        wait_to_click("#deformField1")
        wait_picker_to_show_up()
        pick_today()
        wait_to_click("#deformsubmit")

        try:
            findcss(".has_error")
            raise AssertionError("Should not happen")
        except NoSuchElementException:
            pass

        try:
            findid("error-deformField1", clickable=False)
            raise AssertionError("Should not happen")
        except NoSuchElementException:
            pass

        expected = "%d, %d, %d" % (today.year, today.month, today.day)
        expected = "{'somedate': datetime.date(%s)}" % expected
        self.assertSimilarRepr(findid("captured").text, expected)


class TimeInputWidgetTests(Base, unittest.TestCase):

    url = test_url("/timeinput/")

    def test_render_default(self):
        self.assertTrue("Time" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Time")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid_view("error-deformField1").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid_view("captured").text, "None")

    def test_submit_tooearly(self):
        wait_to_click("#deformField1")
        wait_picker_to_show_up()
        wait_to_click('li[data-pick="0"]')
        submit_date_picker_safe()
        self.assertTrue(findcss(".has-error"))
        self.assertTrue("is earlier than" in findid("error-deformField1").text)
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        wait_to_click("#deformField1")
        wait_picker_to_show_up()
        findxpath('//li[@data-pick="900"]').click()
        submit_date_picker_safe()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertRaises(
            NoSuchElementException, findid_view, "error-deformField1"
        )
        expected = "{'sometime': datetime.time(15, 0)}"
        captured = findid("captured").text
        if captured.startswith("u"):
            captured = captured[1:]
        self.assertEqual(captured, expected)


class DateTimeInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/datetimeinput/")

    def test_render_default(self):
        self.assertEqual(findcss(".required").text, "Date Time")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid("deformField1-date").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-time").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_both_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_time_empty(self):
        wait_to_click("#deformField1-date")
        wait_to_click(".picker__button--today")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Incomplete time")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_date_empty(self):
        wait_to_click("#deformField1-time")
        wait_to_click('li[data-pick="0"]')
        submit_date_picker_safe()
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Incomplete date")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_tooearly(self):
        wait_to_click("#deformField1-time")
        wait_to_click('li[data-pick="0"]')
        wait_to_click("#deformField1-date")

        def diff_month(d1, d2):
            return (d1.year - d2.year) * 12 + d1.month - d2.month + 1

        tooearly = datetime.date(datetime.date.today().year, 1, 1)
        today = datetime.date.today()
        num_months = diff_month(today, tooearly)
        time.sleep(DATE_PICKER_DELAY)
        for _x in range(num_months):
            findcss(".picker__nav--prev").click()
            # Freaking manual timing here again
            time.sleep(0.2)

        wait_to_click(".picker__day")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertTrue("is earlier than" in findid("error-deformField1").text)
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        now = datetime.datetime.now()
        wait_to_click("#deformField1-time")
        wait_to_click('li[data-pick="60"]')
        wait_to_click("#deformField1-date")
        wait_to_click(".picker__button--today")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

        try:
            findid("error-deformField1", clickable=False)
            raise AssertionError("Should not be reached")
        except NoSuchElementException:
            pass

        expected = "%d, %d, %d, %d, %d" % (now.year, now.month, now.day, 1, 0)

        expected = "{'date_time': datetime.datetime(%s" % expected
        # Fails randomly, unknown reason
        for i in range(0, 3):
            try:
                captured = findid_view("captured").text
                if captured.startswith("u"):
                    captured = captured[1:]
                self.assertTrue(
                    captured.startswith(expected), (captured, expected)
                )
            except AssertionError:
                if i < 2:
                    time.sleep(0.2)
                    continue


class DateTimeInputReadonlyTests(Base, unittest.TestCase):
    url = test_url("/datetimeinput_readonly/")

    def test_render_default(self):
        self.assertEqual(findcss(".required").text, "Date Time")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(findid("deformField1").text, "2011-05-05 01:02:00")


class DatePartsWidgetTests(Base, unittest.TestCase):
    url = test_url("/dateparts/")

    def test_render_default(self):
        self.assertTrue("Date" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Date")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField1-day").get_attribute("value"), "")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField1-day").get_attribute("value"), "")
        self.assertTrue(findcss(".has-error"))

    def test_submit_only_year(self):
        findid("deformField1").send_keys("2010")
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Incomplete date")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "2010"
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField1-day").get_attribute("value"), "")
        self.assertTrue(findcss(".has-error"))

    def test_submit_only_year_and_month(self):
        findid("deformField1").send_keys("2010")
        findid("deformField1-month").send_keys("1")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Incomplete date")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "2010"
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), "1"
        )
        self.assertEqual(findid("deformField1-day").get_attribute("value"), "")

    def test_submit_tooearly(self):
        findid("deformField1").send_keys("2008")
        findid("deformField1-month").send_keys("1")
        findid("deformField1-day").send_keys("1")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text,
            "2008-01-01 is earlier than earliest date 2010-01-01",
        )
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "2008"
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), "1"
        )
        self.assertEqual(
            findid("deformField1-day").get_attribute("value"), "1"
        )

    def test_submit_success(self):
        findid("deformField1").send_keys("2010")
        findid("deformField1-month").send_keys("1")
        findid("deformField1-day").send_keys("1")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid("captured").text, "{'date': datetime.date(2010, 1, 1)}"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "2010"
        )
        self.assertEqual(
            findid("deformField1-month").get_attribute("value"), "01"
        )
        self.assertEqual(
            findid("deformField1-day").get_attribute("value"), "01"
        )


class DatePartsReadonlyTests(Base, unittest.TestCase):
    url = test_url("/dateparts_readonly/")

    def test_render_default(self):
        self.assertTrue("Date" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Date")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(findid("deformField1").text, "2010/05/05")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")


class EditFormTests(Base, unittest.TestCase):
    url = test_url("/edit/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "42"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "number"
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("deformField3").get_attribute("name"), "name")
        self.assertEqual(findid("deformField4").get_attribute("value"), "2010")
        self.assertEqual(findid("deformField4").get_attribute("name"), "year")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), "04"
        )
        self.assertEqual(
            findid("deformField4-month").get_attribute("name"), "month"
        )
        self.assertEqual(
            findid("deformField4-day").get_attribute("value"), "09"
        )
        self.assertEqual(
            findid("deformField4-day").get_attribute("name"), "day"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField3").send_keys("name")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "42"
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "name")
        self.assertEqual(findid("deformField4").get_attribute("value"), "2010")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), "04"
        )
        self.assertEqual(
            findid("deformField4-day").get_attribute("value"), "09"
        )
        self.assertSimilarRepr(
            findid("captured").text,
            (
                "{'mapping': {'date': datetime.date(2010, 4, 9), "
                "'name': 'name'}, 'number': 42}"
            ),
        )


class MappingWidgetTests(Base, unittest.TestCase):
    url = test_url("/mapping/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("deformField4").get_attribute("value"), "")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField4-day").get_attribute("value"), "")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_invalid_number(self):
        findid("deformField1").send_keys("notanumber")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid("error-deformField1").text, '"notanumber" is not a number'
        )
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_invalid_date(self):
        findid("deformField1").send_keys("1")
        findid("deformField3").send_keys("name")
        findid("deformField4").send_keys("year")
        findid("deformField4-month").send_keys("month")
        findid("deformField4-day").send_keys("day")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField4").text, "Invalid date")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "1"
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "name")
        self.assertEqual(findid("deformField4").get_attribute("value"), "year")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), "mo"
        )
        self.assertEqual(
            findid("deformField4-day").get_attribute("value"), "da"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField1").send_keys("1")
        findid("deformField3").send_keys("name")
        findid("deformField4").send_keys("2010")
        findid("deformField4-month").send_keys("1")
        findid("deformField4-day").send_keys("1")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "1"
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "name")
        self.assertEqual(findid("deformField4").get_attribute("value"), "2010")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), "01"
        )
        self.assertEqual(
            findid("deformField4-day").get_attribute("value"), "01"
        )
        self.assertSimilarRepr(
            findid("captured").text,
            (
                "{'mapping': {'date': datetime.date(2010, 1, 1), "
                "'name': 'name'}, 'number': 1}"
            ),
        )


class FieldDefaultTests(Base, unittest.TestCase):
    url = test_url("/fielddefaults/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "Grandaddy"
        )
        self.assertEqual(
            findid("deformField2").get_attribute("value"),
            "Just Like the Fambly Cat",
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "Grandaddy"
        )
        self.assertEqual(
            findid("deformField2").get_attribute("value"),
            "Just Like the Fambly Cat",
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("error-deformField3").text, "Required")

    def test_submit_success(self):
        findid("deformField1").clear()
        findid("deformField1").send_keys("abc")
        findid("deformField2").clear()
        findid("deformField2").send_keys("def")
        findid("deformField3").clear()
        findid("deformField3").send_keys("ghi")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "def")
        self.assertEqual(findid("deformField3").get_attribute("value"), "ghi")
        self.assertSimilarRepr(
            findid("captured").text,
            "{'album': 'def', 'artist': 'abc', 'song': 'ghi'}",
        )


class NonRequiredFieldTests(Base, unittest.TestCase):
    url = test_url("/nonrequiredfields/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success_required_filled_notrequired_empty(self):
        findid("deformField1").send_keys("abc")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "")
        self.assertSimilarRepr(
            findid("captured").text, "{'notrequired': '', 'required': 'abc'}"
        )

    def test_submit_success_required_and_notrequired_filled(self):
        findid("deformField1").send_keys("abc")
        findid("deformField2").send_keys("def")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "def")
        self.assertSimilarRepr(
            findid("captured").text,
            "{'notrequired': 'def', 'required': 'abc'}",
        )


class HiddenFieldWidgetTests(Base, unittest.TestCase):
    url = test_url("/hidden_field/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid("deformField1", clickable=False).get_attribute("value"),
            "true",
        )
        self.assertEqual(findid("captured").text, "None")

    def test_render_submitted(self):
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid("deformField1", clickable=False).get_attribute("value"),
            "true",
        )
        self.assertEqual(findid("captured").text, "{'sneaky': True}")


class HiddenmissingTests(Base, unittest.TestCase):
    url = test_url("/hiddenmissing/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid("deformField1", clickable=False).get_attribute("value"), ""
        )
        self.assertEqual(
            findid("deformField2", clickable=False).get_attribute("value"), ""
        )
        self.assertEqual(findid("captured").text, "None")

    def test_render_submitted(self):
        findid("deformField1").send_keys("yup")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid("deformField1", clickable=False).get_attribute("value"),
            "yup",
        )
        self.assertSimilarRepr(
            findid("captured").text,
            "{'number': <colander.null>, 'title': 'yup'}",
        )


class FileUploadTests(Base, unittest.TestCase):
    url = test_url("/file/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findcss("input[type=file]").get_attribute("value"), ""
        )
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), ""
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_filled(self):

        # submit one first
        path, filename = _getFile()
        findcss("input[type=file]").send_keys(path)
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename
        )
        wait_to_click("#deformsubmit")

        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findcss("input[type=file]").get_attribute("value"), ""
        )
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename
        )
        self.assertTrue(filename in findid("captured").text)
        uid = findcss("[name=uid]").get_attribute("value")
        self.assertTrue(uid in findid("captured").text)

        # resubmit without entering a new filename should not change the file
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename
        )
        self.assertEqual(findcss("[name=uid]").get_attribute("value"), uid)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile("validation.py")
        findcss("input[type=file]").send_keys(path2)
        wait_to_click("#deformsubmit")
        got_name = findcss(".upload-filename").get_attribute("value")
        self.assertEqual(got_name, filename2)
        self.assertTrue("filename" in findid("captured").text)
        self.assertTrue(uid in findid("captured").text)


class FileUploadReadonlyTests(Base, unittest.TestCase):
    url = test_url("/file_readonly/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findid("deformField1").text, "leavesofgrass.png")
        self.assertEqual(findid("captured").text, "None")


class InterFieldValidationTests(Base, unittest.TestCase):
    url = test_url("/interfield/")

    def test_render_default(self):
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid_view("deformField2").get_attribute("value"), ""
        )
        self.assertEqual(findid_view("captured").text, "None")

    def test_submit_both_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid_view("error-deformField1").text, "Required")
        self.assertEqual(findid_view("error-deformField2").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid_view("deformField2").get_attribute("value"), ""
        )
        self.assertEqual(findid_view("captured").text, "None")

    def test_submit_one_empty(self):
        findid("deformField1").send_keys("abc")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertRaises(
            NoSuchElementException, findid_view, "error-deformField1"
        )
        self.assertEqual(findid_view("error-deformField2").text, "Required")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(
            findid_view("deformField2").get_attribute("value"), ""
        )
        self.assertEqual(findid_view("captured").text, "None")

    def test_submit_first_doesnt_start_with_second(self):
        findid("deformField1").send_keys("abc")
        findid("deformField2").send_keys("def")
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertRaises(
            NoSuchElementException, findid_view, "error-deformField1"
        )
        self.assertEqual(
            findid("error-deformField2").text, "Must start with name abc"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "def")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField1").send_keys("abc")
        findid("deformField2").send_keys("abcdef")
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertRaises(
            NoSuchElementException, findid_view, "error-deformField1"
        )
        self.assertRaises(
            NoSuchElementException, findid_view, "error-deformField1"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abc"
        )
        self.assertEqual(
            findid("deformField2").get_attribute("value"), "abcdef"
        )
        self.assertEqual(
            eval(findid("captured").text), {"name": "abc", "title": "abcdef"}
        )


class InternationalizationTests(Base, unittest.TestCase):
    url = test_url("/i18n/")

    def setUp(self):
        pass  # each tests has a different url

    def test_render_default(self):
        browser.get(self.url)
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findcss("label").text, "A number between 1 and 10")
        self.assertEqual(findid("deformsubmit").text, "Submit")

    def test_render_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findcss("label").text, "A number between 1 and 10")
        self.assertEqual(findid("deformsubmit").text, "Submit")

    def test_render_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findcss("label").text, u"Число между 1 и 10")
        self.assertEqual(findid("deformsubmit").text, u"отправить")

    def test_submit_empty_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".alert-danger").text,
            "There was a problem with your submission\n"
            "Errors have been highlighted below",
        )
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findcss("label").text, "A number between 1 and 10")
        self.assertEqual(findid("deformsubmit").text, "Submit")

    def test_submit_empty_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".alert-danger .error-msg-lbl").text,
            u"Данные которые вы предоставили содержат ошибку",
        )
        self.assertEqual(findid("error-deformField1").text, u"Требуется")
        self.assertEqual(findcss("label").text, u"Число между 1 и 10")
        self.assertEqual(findid("deformsubmit").text, u"отправить")

    def test_submit_toolow_en(self):
        browser.get("%s?_LOCALE_=en" % self.url)
        findid("deformField1").send_keys("0")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".alert-danger").text,
            "There was a problem with your submission\n"
            "Errors have been highlighted below",
        )
        self.assertEqual(
            findid("error-deformField1").text, "0 is less than minimum value 1"
        )
        self.assertEqual(findcss("label").text, "A number between 1 and 10")
        self.assertEqual(findid("deformsubmit").text, "Submit")

    def test_submit_toolow_ru(self):
        browser.get("%s?_LOCALE_=ru" % self.url)
        findid("deformField1").send_keys("0")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".alert-danger .error-msg-lbl").text,
            u"Данные которые вы предоставили содержат ошибку",
        )
        self.assertEqual(findid("error-deformField1").text, u"0 меньше чем 1")
        self.assertEqual(findcss("label").text, u"Число между 1 и 10")
        self.assertEqual(findid("deformsubmit").text, u"отправить")


class PasswordWidgetTests(Base, unittest.TestCase):
    url = test_url("/password/")

    def test_render_submit_success(self):
        findid("deformField1").send_keys("abcdef123")
        wait_to_click("#deformsubmit")
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertSimilarRepr(
            findid("captured").text, "{'password': u'abcdef123'}"
        )


class PasswordWidgetRedisplayTests(Base, unittest.TestCase):
    url = test_url("/password_redisplay/")

    def test_render_default(self):
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(findid("captured").text, "None")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findcss(".required").text, "Password")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )

    def test_render_submit_empty(self):
        wait_to_click("#deformsubmit")
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(findcss(".required").text, "Password")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("error-deformField1").text, "Required")

    def test_render_submit_success(self):
        findid("deformField1").send_keys("abcdef123")
        wait_to_click("#deformsubmit")
        self.assertTrue("Password" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "abcdef123"
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertSimilarRepr(
            findid("captured").text, "{'password': u'abcdef123'}"
        )


class RadioChoiceWidgetTests(Base, unittest.TestCase):
    url = test_url("/radiochoice/")

    def test_render_default(self):
        self.assertTrue("Password" in browser.page_source)
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findcss(".required").text, "Choose your pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_unchecked(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        wait_to_click("#deformsubmit")
        self.assertTrue(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertSimilarRepr(
            findid("captured").text, "{'pepper': u'habanero'}"
        )


class RadioChoiceWidgetInlineTests(Base, unittest.TestCase):
    url = test_url("/radiochoice_inline/")

    def test_render_default(self):
        self.assertTrue("Password" in browser.page_source)
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findcss(".required").text, "Choose your pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_unchecked(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertFalse(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        wait_to_click("#deformsubmit")
        self.assertTrue(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertSimilarRepr(
            findid("captured").text, "{'pepper': u'habanero'}"
        )


class RadioChoiceWidgetIntTests(RadioChoiceWidgetTests):
    url = test_url("/radiochoice_int/")

    def test_submit_one_checked(self):
        findid("deformField1-0").click()
        wait_to_click("#deformsubmit")
        self.assertTrue(findid("deformField1-0").is_selected())
        self.assertFalse(findid("deformField1-1").is_selected())
        self.assertFalse(findid("deformField1-2").is_selected())
        self.assertSimilarRepr(findid("captured").text, "{'pepper': 0}")


class RadioChoiceReadonlyTests(Base, unittest.TestCase):
    url = test_url("/radiochoice_readonly/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1-1").text, "Jalapeno")
        self.assertEqual(findcss(".required").text, "Pepper")
        self.assertEqual(findid("captured").text, "None")


class ReadOnlySequenceOfMappingTests(Base, unittest.TestCase):
    url = test_url("/readonly_sequence_of_mappings/")

    def test_render_default(self):
        self.assertEqual(findid("deformField6").text, "name1")
        self.assertEqual(findid("deformField7").text, "23")
        self.assertEqual(findid("deformField9").text, "name2")
        self.assertEqual(findid("deformField10").text, "25")


class SequenceOfRadioChoicesTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_radiochoices/")

    def test_render_default(self):
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Pepper Chooser"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Pepper Chooser"
        )
        self.assertEqual(findid("captured").text, "{'peppers': []}")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_two_filled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findxpaths("//input")[4].click()
        findxpaths("//input")[10].click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text),
            {"peppers": ["habanero", "jalapeno"]},
        )


class SequenceOfDefaultedSelectsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects/")

    def test_render_default(self):
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Pepper Chooser"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Pepper Chooser"
        )
        self.assertEqual(findid("captured").text, "{'peppers': []}")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_two_filled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text),  # should be 2 values, both defaults
            {"peppers": ["jalapeno", "jalapeno"]},
        )


class SequenceOfDefaultedSelectsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_defaulted_selects_with_initial_item/")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Pepper Chooser"
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text),  # should be 1 value (min_len 1)
            {"peppers": ["jalapeno"]},
        )

    def test_submit_one_added(self):
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text),  # should be 2 values, both defaults
            {"peppers": ["jalapeno", "jalapeno"]},
        )


class SequenceOfFileUploadsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1-addtext").text, "Add Upload")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("deformField1-addtext").text, "Add Upload")
        self.assertEqual(findid("captured").text, "{'uploads': []}")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_upload_one_success(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpath('//input[@name="upload"]').send_keys(path)
        wait_to_click("#deformsubmit")

        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findcss("input[type=file]").get_attribute("value"), ""
        )
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename
        )
        uid = findcss("[name=uid]").get_attribute("value")
        self.assertTrue(filename in findid("captured").text)
        self.assertTrue(uid in findid("captured").text)

    def test_upload_multi_interaction(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpath('//input[@name="upload"]').send_keys(path)
        wait_to_click("#deformsubmit")

        self.assertRaises(NoSuchElementException, findcss, ".has-error")

        self.assertEqual(
            findcss("input[type=file]").get_attribute("value"), ""
        )
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename
        )
        uid = findcss("[name=uid]").get_attribute("value")
        self.assertTrue(filename in findid("captured").text)
        self.assertTrue(uid in findid("captured").text)

        # resubmit without entering a new filename should not change the file
        wait_to_click("#deformsubmit")
        self.assertTrue(filename in findid("captured").text)
        self.assertTrue(uid in findid("captured").text)

        # resubmit after entering a new filename should change the file
        path2, filename2 = _getFile("validation.py")
        findcss("input[type=file]").send_keys(path2)
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findcss(".upload-filename").get_attribute("value"), filename2
        )
        self.assertTrue(filename2 in findid("captured").text)

        # add a new file
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="upload"]')[1].send_keys(path)
        wait_to_click("#deformsubmit")
        upload_filenames = findcsses(".upload-filename")
        self.assertEqual(upload_filenames[0].get_attribute("value"), filename2)
        self.assertEqual(upload_filenames[1].get_attribute("value"), filename)

        # resubmit should not change either file
        wait_to_click("#deformsubmit")
        upload_filenames = findcsses(".upload-filename")
        self.assertEqual(upload_filenames[0].get_attribute("value"), filename2)
        self.assertEqual(upload_filenames[1].get_attribute("value"), filename)

        # remove a file
        findid("deformField4-close").click()
        wait_to_click("#deformsubmit")
        upload_filenames = findcsses(".upload-filename")
        self.assertEqual(upload_filenames[0].get_attribute("value"), filename2)
        self.assertEqual(len(upload_filenames), 1)


class SequenceOfFileUploadsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_fileuploads_with_initial_item/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1-addtext").text, "Add Upload")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_upload_one_success(self):
        path, filename = _getFile()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="upload"]')[0].send_keys(path)
        upload_filenames = [
            elem.get_attribute("value")
            for elem in findcsses(".upload-filename")
        ]
        self.assertEqual(upload_filenames[0], filename)
        self.assertEqual(upload_filenames[1], "")
        findxpaths('//input[@name="upload"]')[1].send_keys(path)
        wait_to_click("#deformsubmit")

        # first element present
        upload_filenames = [
            elem.get_attribute("value")
            for elem in findcsses(".upload-filename")
        ]
        uid_elems = findcsses("[name=uid]")
        self.assertEqual(upload_filenames[0], filename)
        uid = uid_elems[0].get_attribute("value")
        self.assertTrue(uid in findid("captured").text)

        # second element present
        self.assertEqual(upload_filenames[1], filename)
        uid = uid_elems[1].get_attribute("value")
        self.assertTrue(uid in findid("captured").text)


class SequenceOfMappingsTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1-addtext").text, "Add Person")
        self.assertEqual(findid("captured").text, "None")
        self.assertTrue(findcss(".deform-proto"))

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("deformField1-addtext").text, "Add Person")
        self.assertEqual(findid("captured").text, "{'people': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField6").text, "Required")
        self.assertEqual(findid("error-deformField7").text, "Required")
        self.assertEqual(findid("error-deformField9").text, "Required")
        self.assertEqual(findid("error-deformField10").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_complex_interaction(self):
        findid("deformField1-seqAdd").click()

        findxpath('//input[@name="name"]').send_keys("name")
        findxpath('//input[@name="age"]').send_keys("23")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {"people": [{"name": "name", "age": 23}]},
        )

        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].clear()
        findxpaths('//input[@name="name"]')[0].send_keys("name-changed")
        findxpaths('//input[@name="name"]')[1].send_keys("name2")
        findxpaths('//input[@name="age"]')[0].clear()
        findxpaths('//input[@name="age"]')[0].send_keys("24")
        findxpaths('//input[@name="age"]')[1].send_keys("26")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {
                "people": [
                    {"name": "name-changed", "age": 24},
                    {"name": "name2", "age": 26},
                ]
            },
        )

        findid("deformField5-close").click()  # remove the first mapping
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {"people": [{"name": "name2", "age": 26}]},
        )


class SequenceOfMappingsWithInitialItemTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_mappings_with_initial_item/")

    def test_render_default(self):
        self.assertTrue(findcss(".deform-proto"))
        self.assertEqual(findid("deformField1-addtext").text, "Add Person")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField6").text, "Required")
        self.assertEqual(findid("error-deformField7").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_add_one(self):
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].send_keys("name0")
        findxpaths('//input[@name="name"]')[1].send_keys("name1")
        findxpaths('//input[@name="age"]')[0].send_keys("23")
        findxpaths('//input[@name="age"]')[1].send_keys("25")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {
                "people": [
                    {"name": "name0", "age": 23},
                    {"name": "name1", "age": 25},
                ]
            },
        )


class SequenceOfAutocompletes(Base, unittest.TestCase):
    url = test_url("/sequence_of_autocompletes/")

    def test_render_default(self):
        self.assertEqual(findid("captured").text, "None")
        self.assertTrue("Texts" in browser.page_source)
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")
        self.assertEqual(findid("captured").text, "{'texts': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_two_filled(self):
        action_chains_on_id("deformField1-seqAdd").click().perform()
        input_text = browser.find_elements_by_xpath('//input[@name="text"]')
        ActionChains(browser).move_to_element(input_text[0]).click().send_keys(
            "bar"
        ).send_keys(Keys.TAB).perform()
        action_chains_on_id("deformField1-seqAdd").click().perform()
        input_text = browser.find_elements_by_xpath('//input[@name="text"]')
        ActionChains(browser).move_to_element(input_text[1]).click().send_keys(
            "baz"
        ).click().perform()
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text), {"texts": ["bar", "baz"]}
        )


class SequenceOfDateInputs(Base, unittest.TestCase):
    url = test_url("/sequence_of_dateinputs/")

    def test_render_default(self):
        self.assertTrue("Dates" in browser.page_source)
        self.assertEqual(findid("deformField1-addtext").text, "Add Date")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("deformField1-addtext").text, "Add Date")
        self.assertSimilarRepr(findid("captured").text, "{'dates': []}")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_filled(self):
        action_chains_on_id("deformField1-seqAdd").click().perform()
        action_chains_on_xpath('//input[@name="date"]').click().perform()
        wait_picker_to_show_up()
        findcss(".picker__button--today").click()
        submit_date_picker_safe()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(
            findid("captured").text.startswith("{'dates': [datetime.date")
        )


class SequenceOfConstrainedLengthTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_constrained_len/")

    def test_render_default(self):
        self.assertTrue("At Least 2" in browser.page_source)
        self.assertEqual(findid("deformField1-addtext").text, "Add Name")
        self.assertEqual(findid("captured").text, "None")
        # default 2 inputs rendered
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("deformField4").get_attribute("value"), "")

    def test_add_and_remove(self):
        self.assertEqual(findid("deformField1-addtext").text, "Add Name")
        findid("deformField3").send_keys("hello1")
        findid("deformField4").send_keys("hello2")
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findxpaths('//input[@name="name"]')[2].send_keys("hello3")
        findxpaths('//input[@name="name"]')[3].send_keys("hello4")

        self.assertFalse(findid_view("deformField1-seqAdd").is_displayed())
        findid("deformField3-close").click()
        self.assertTrue(findid_view("deformField1-seqAdd").is_displayed())
        findid("deformField1-seqAdd").click()
        self.assertFalse(findid_view("deformField1-seqAdd").is_displayed())
        findxpaths('//input[@name="name"]')[3].send_keys("hello5")
        wait_to_click("#deformsubmit")
        self.assertFalse(findid_view("deformField1-seqAdd").is_displayed())
        self.assertEqual(
            eval(findid("captured").text),
            {"names": ["hello2", "hello3", "hello4", "hello5"]},
        )


class SequenceOfRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_richtext/")

    def test_render_default(self):
        self.assertTrue("Texts" in browser.page_source)
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")
        self.assertEqual(findid("captured").text, "{'texts': []}")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_filled(self):
        findid("deformField1-seqAdd").click()
        browser.switch_to_frame(browser.find_element_by_tag_name("iframe"))
        findid("tinymce").click()
        findid("tinymce").send_keys("yo")
        browser.switch_to_default_content()
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text), {"texts": ["<p>yo</p>"]}
        )


@flaky
class SequenceOfMaskedTextInputs(Base, unittest.TestCase):
    url = test_url("/sequence_of_masked_textinputs/")

    def test_render_default(self):
        self.assertTrue("Texts" in browser.page_source)
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_none_added(self):
        findid("deformsubmit").click()
        self.assertEqual(findid("deformField1-addtext").text, "Add Text")
        self.assertEqual(findid("captured").text, "{'texts': []}")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_two_unfilled(self):
        findid("deformField1-seqAdd").click()
        findid("deformField1-seqAdd").click()
        findid("deformsubmit").click()
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_filled(self):
        browser.get(self.url)
        action_chains_on_id("deformField1-seqAdd").click().perform()

        action_chains_on_xpath('//input[@name="text"]').click().send_keys(
            Keys.HOME
        ).send_keys(Keys.HOME).send_keys("140118866").perform()

        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'texts': ['140-11-8866']}")


@flaky
class SelectWidgetTests(Base, unittest.TestCase):
    url = test_url("/select/")
    submit_selected_captured = (
        "{'pepper': 'habanero'}",
        "{'pepper': 'habanero'}",
    )

    def test_render_default(self):
        self.assertTrue("Pepper" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "pepper")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertEqual(
            [o.text for o in options],
            ["- Select -", "Habanero", "Jalapeno", "Chipotle"],
        )
        self.assertEqual(findcss(".required").text, "Pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_default(self):
        findid("deformsubmit").click()
        self.assertTrue("Pepper" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "pepper")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_selected(self):
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        options[1].click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        wait_until_visible("#deformField1")
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        # TODO: The form state is not carried over POST in demos and this
        # is disabled for self.assertTrue(options[1].is_selected())
        text = findid("captured").text

        assert "pepper" in text


class SelectWidgetWithSizeTests(SelectWidgetTests):
    url = test_url("/select_with_size/")


class SelectWidgetWithUnicodeTests(SelectWidgetTests):
    url = test_url("/select_with_unicode/")
    submit_selected_captured = (
        "{'pepper': '\u30cf\u30d0\u30cd\u30ed'}",
        "{'pepper': u'\\u30cf\\u30d0\\u30cd\\u30ed'}",
    )


class SelectWidgetMultipleTests(Base, unittest.TestCase):
    url = test_url("/select_with_multiple/")

    def test_submit_selected(self):
        select = findid("deformField1")
        self.assertTrue(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        options[0].click()
        options[2].click()

        findid("deformsubmit").click()

        captured_default = {"pepper": set(["chipotle", "habanero"])}
        self.assertEqual(eval(findid("captured").text), captured_default)
        self.assertRaises(NoSuchElementException, findcss, ".has-error")


class SelectWidgetIntegerTests(Base, unittest.TestCase):
    url = test_url("/select_integer/")

    def test_render_default(self):
        self.assertTrue("Number" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "number")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options], ["- Select -", "Zero", "One", "Two"]
        )
        self.assertEqual(findcss(".required").text, "Number")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_default(self):
        findid("deformsubmit").click()
        self.assertTrue("Number" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "number")
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_selected(self):
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        options[1].click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        # TODO: This is not captured in new demos so we don't test it here
        # self.assertTrue(options[1].is_selected())
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'number': 0}")


class SelectWidgetWithOptgroupTests(Base, unittest.TestCase):
    url = test_url("/select_with_optgroup/")

    def test_render_default(self):
        self.assertTrue("Musician" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "musician")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [
                "Select your favorite musician",
                "Jimmy Page",
                "Jimi Hendrix",
                "Billy Cobham",
                "John Bonham",
            ],
        )
        self.assertEqual(findcss(".required").text, "Musician")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(len(findxpaths("//optgroup")), 2)

    def test_submit_selected(self):
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        options[1].click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        # TODO: DEmo no longer carries over the submission state, not tested
        # self.assertTrue(options[1].is_selected())
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'musician': 'page'}")


class SelectWidgetWithOptgroupAndLabelTests(SelectWidgetWithOptgroupTests):
    url = test_url("/select_with_optgroup_and_label_attributes/")

    def test_render_default(self):
        self.assertTrue("Musician" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "musician")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [
                "Select your favorite musician",
                "Guitarists - Jimmy Page",
                "Guitarists - Jimi Hendrix",
                "Drummers - Billy Cobham",
                "Drummers - John Bonham",
            ],
        )
        self.assertEqual(findcss(".required").text, "Musician")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(len(findxpaths("//optgroup")), 2)

    def test_submit_selected(self):
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        options[1].click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        select = findid("deformField1")
        options = select.find_elements_by_tag_name("option")
        # TODO: Not currently carried over in demo
        # self.assertTrue(options[1].is_selected())
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'musician': 'page'}")


class SelectReadonlyTests(Base, unittest.TestCase):
    url = test_url("/select_readonly/")

    def test_render_default(self):
        musician = findid("deformField1-2-0")
        self.assertEqual(musician.text, "Billy Cobham")
        multi1 = findid("deformField2-1-0")
        self.assertEqual(multi1.text, "Jimmy Page")
        multi2 = findid("deformField2-2-0")
        self.assertEqual(multi2.text, "Billy Cobham")
        self.assertEqual(findid("captured").text, "None")


class Select2WidgetTests(Base, unittest.TestCase):
    url = test_url("/select2/")
    first_selected_captured = "{'pepper': 'habanero'}"
    second_selected_captured = "{'pepper': 'jalapeno'}"

    def test_render_default(self):
        self.assertTrue("Pepper" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "pepper")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            ["- Select -", "Habanero", "Jalapeno", "Chipotle"],
        )
        self.assertEqual(findcss(".required").text, "Pepper")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_default(self):
        findid("deformsubmit").click()
        self.assertTrue("Pepper" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "pepper")
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_selected(self):
        action_chains_xpath_on_select(
            "//select[@name='pepper']/option"
        ).click().send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()

        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertTrue(
            findid("captured").text in self.first_selected_captured
        )

        action_chains_xpath_on_select(
            "//select[@name='pepper']/option[@selected='selected']"
        ).click().send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()
        findid("deformsubmit").click()
        self.assertTrue(
            findid("captured").text in self.second_selected_captured
        )


class Select2WidgetMultipleTests(Base, unittest.TestCase):
    url = test_url("/select2_with_multiple/")

    def test_submit_selected(self):
        action_chains_xpath_on_select(
            "//select[@name='pepper']/option"
        ).click().send_keys(Keys.ARROW_DOWN).send_keys(
            Keys.ARROW_DOWN
        ).send_keys(
            Keys.ARROW_DOWN
        ).send_keys(
            Keys.ENTER
        ).perform()

        time.sleep(1)

        action_chains_xpath_on_select(
            "//option[contains(text(), 'Chipotle')]"
        ).click().send_keys(Keys.ARROW_UP).send_keys(Keys.ARROW_UP).send_keys(
            Keys.ARROW_UP
        ).send_keys(
            Keys.ENTER
        ).perform()

        findid("deformsubmit").click()

        captured_default = {"pepper": set(["chipotle", "habanero"])}
        self.assertEqual(eval(findid("captured").text), captured_default)
        self.assertRaises(NoSuchElementException, findcss, ".has-error")


class Select2WidgetWithOptgroupTests(Base, unittest.TestCase):
    url = test_url("/select2_with_optgroup/")

    first_selected_captured = "{'musician': 'page'}"
    second_selected_captured = "{'musician': 'bonham'}"

    def test_render_default(self):
        self.assertTrue("Musician" in browser.page_source)
        select = findid("deformField1")
        self.assertEqual(select.get_attribute("name"), "musician")
        self.assertFalse(select.get_attribute("multiple"))
        options = select.find_elements_by_tag_name("option")
        self.assertTrue(options[0].is_selected())
        self.assertEqual(
            [o.text for o in options],
            [
                "Select your favorite musician",
                "Jimmy Page",
                "Jimi Hendrix",
                "Billy Cobham",
                "John Bonham",
            ],
        )
        self.assertEqual(findcss(".required").text, "Musician")
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(len(findxpaths("//optgroup")), 2)

    def test_submit_selected(self):
        action_chains_xpath_on_select(
            "//select[@name='musician']/option"
        ).click().send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()

        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        captured = findid("captured").text
        self.assertSimilarRepr(captured, self.first_selected_captured)

        time.sleep(1)

        action_chains_xpath_on_select(
            "//option[contains(text(), 'Page')]"
        ).click().send_keys(Keys.ARROW_DOWN).send_keys(
            Keys.ARROW_DOWN
        ).send_keys(
            Keys.ARROW_DOWN
        ).send_keys(
            Keys.ENTER
        ).perform()
        findid("deformsubmit").click()
        self.assertTrue(
            findid("captured").text in self.second_selected_captured
        )


class Select2TagsWidgetTests(Base, unittest.TestCase):
    url = test_url("/select2_with_tags/")

    def test_submit_new_option(self):
        # open select search field
        findcss(".select2-container").click()

        # options list is empty
        self.assertSimilarRepr(
            findid("select2-deformField1-results").text, "No results found"
        )

        # type a value in selec2 search
        (
            findid("public")
            .find_element_by_css_selector(".select2-search__field")
            .send_keys("hello\n")
        )

        # after form submission typed value appear in captured
        findid("deformsubmit").click()
        captured = findid("captured").text
        self.assertSimilarRepr(
            captured, "{'pepper': 'hello'}",
        )


class Select2WidgetTagsMultipleTests(Base, unittest.TestCase):
    url = test_url("/select2_with_tags_and_multiple/")

    def test_submit_new_options(self):
        # multiple submission is activated
        self.assertTrue(findid("deformField1").get_attribute("multiple"))

        # options list is empty
        findid("item-deformField1").click()
        self.assertSimilarRepr(
            findid("select2-deformField1-results").text, "No results found"
        )

        # adding values to select field
        for value in ("hello", "qwerty", "hello"):
            # open select search field
            findid("item-deformField1").click()
            # type values in selec2 search
            (
                findid("public")
                .find_element_by_css_selector(".select2-search__field")
                .send_keys(value + "\n")
            )

        # after form submission typed value appear in captured
        findid("deformsubmit").click()
        captured = findid("captured").text
        expected = "{'pepper': {'hello', 'qwerty'}}"
        if PY3:
            captured = sort_set_values(captured)
        self.assertSimilarRepr(captured, expected)


class SelectWithDefaultTests(Base, unittest.TestCase):

    url = test_url("/select_with_default/")

    def test_default_selected(self):
        """Make sure the supplied default value for select is honoured."""

        elem = findcss("option[value='jalapeno']")
        assert elem.get_attribute("selected") is not None

        elem = findcss("option[value='chipotle']")
        assert elem.get_attribute("selected") is None


class SelectWithMultipleDefaultTests(Base, unittest.TestCase):

    url = test_url("/select_with_multiple_default_integers/")

    def test_default_selected(self):
        """Make sure the supplied default value for select is honoured for multiple values."""  # noQA

        elem = findcss("option[value='1']")
        assert elem.get_attribute("selected") is not None

        elem = findcss("option[value='2']")
        assert elem.get_attribute("selected") is not None

        elem = findcss("option[value='3']")
        assert elem.get_attribute("selected") is None


class TextInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput/")

    def test_render_default(self):
        self.assertTrue("Text" in browser.page_source)
        element = findid("deformField1")
        self.assertEqual(element.get_attribute("name"), "text")
        self.assertEqual(element.get_attribute("type"), "text")
        self.assertEqual(element.get_attribute("value"), "")
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformsubmit").click()
        element = findid("deformField1")
        self.assertEqual(element.get_attribute("name"), "text")
        self.assertEqual(element.get_attribute("type"), "text")
        self.assertEqual(element.get_attribute("value"), "")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("captured").text, "None")

    def test_submit_filled(self):
        findid("deformField1").send_keys("hello")
        findid("deformsubmit").click()
        element = findid("deformField1")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(element.get_attribute("value"), "hello")
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'text': u'hello'}")


class TextInputWithCssClassWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput_with_css_class/")

    def test_render_default(self):
        findcss(".deform-widget-with-style")


class MoneyInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/money_input/")

    def test_render_default(self):
        findid("deformField1").send_keys("12")
        self.assertTrue("Greenbacks" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "greenbacks"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("type"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "0.12"
        )
        self.assertEqual(findcss(".required").text, "Greenbacks")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformField1").send_keys("12")
        findid("deformsubmit").click()
        self.assertEqual(
            findid("captured").text, "{'greenbacks': Decimal('0.12')}"
        )

    def test_submit_filled(self):
        action_chains_on_id("deformField1").send_keys("1").perform()

        action_chains_on_id("deformField1").send_keys(
            5 * Keys.ARROW_LEFT
        ).perform()

        action_chains_on_id("deformField1").send_keys("10").perform()

        findid("deformsubmit").click()
        self.assertEqual(
            findid("captured").text, "{'greenbacks': Decimal('100.01')}"
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")


class AutocompleteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_input/")

    def test_render_default(self):
        self.assertTrue("Autocomplete Input Widget" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("type"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("captured").text, "None")

    def test_submit_filled(self):
        findid("deformField1").send_keys("ba")
        self.assertTrue(findxpath('//p[text()="baz"]').is_displayed())
        findid("deformField1").send_keys("r")
        findcss(".tt-suggestion").click()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        text = findid("captured").text
        # py2/py3 compat, py2 adds extra u prefix
        self.assertTrue("bar" in text)

    def test_ampersand(self):
        findid("deformField1").send_keys("foo")
        self.assertTrue(findxpath('//p[text()="foo & bar"]').is_displayed())
        action_chains_on_css_selector(".tt-suggestion").click().perform()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        text = findid("captured").text
        # py2/py3 compat, py2 adds extra u prefix
        self.assertTrue("foo & bar" in text)

    def test_less_than(self):
        findid("deformField1").send_keys("one")
        self.assertTrue(findxpath('//p[text()="one < two"]').is_displayed())
        findid("deformField1").send_keys(Keys.ARROW_DOWN)
        findid("deformField1").send_keys(Keys.ENTER)
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        text = findid("captured").text
        # py2/py3 compat, py2 adds extra u prefix
        self.assertTrue("one < two" in text)


class AutocompleteRemoteInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/autocomplete_remote_input/")

    def test_render_default(self):
        self.assertTrue(
            "Autocomplete Input Widget (with Remote Data Source)"
            in browser.page_source
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("type"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_filled(self):
        findid("deformField1").send_keys("t")

        time.sleep(0.2)
        self.assertTrue(findxpath('//p[text()="two"]').is_displayed())
        self.assertTrue(findxpath('//p[text()="three"]').is_displayed())

        findid("deformField1").send_keys(Keys.ARROW_DOWN)
        findid("deformField1").send_keys(Keys.ENTER)
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

        # py2/py3 compat
        self.assertTrue("two" in findid("captured").text)


class TextAreaWidgetTests(Base, unittest.TestCase):
    url = test_url("/textarea/")

    def test_render_default(self):
        self.assertTrue("Text" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("rows"), "10"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("cols"), "60"
        )
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertTrue(findcss(".has-error"))

    def test_submit_filled(self):
        findid("deformField1").send_keys("hello")
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(findid("captured").text, "{'text': 'hello'}")


class TextAreaReadonlyTests(Base, unittest.TestCase):
    url = test_url("/textarea_readonly/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1").text, "text")
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")


class DelayedRichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/delayed_richtext/")

    def test_submit_filled(self):
        findcss(".tinymce-preload").click()
        time.sleep(0.5)
        browser.switch_to_frame(browser.find_element_by_tag_name("iframe"))
        findid("tinymce").click()
        findid("tinymce").send_keys("hello")
        browser.switch_to_default_content()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text), {"text": "<p>hello</p>"}
        )


class RichTextWidgetTests(Base, unittest.TestCase):
    url = test_url("/richtext/")

    def test_render_default(self):
        self.assertTrue("Text" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "text"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_empty(self):
        findid("deformsubmit").click()
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertTrue(findcss(".has-error"))
        self.assertEqual(findid("captured").text, "None")

    def test_submit_filled(self):
        browser.switch_to_frame(browser.find_element_by_tag_name("iframe"))
        findid("tinymce").click()
        findid("tinymce").send_keys("hello")
        browser.switch_to_default_content()
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            eval(findid("captured").text), {"text": "<p>hello</p>"}
        )


class RichTextWidgetInternationalized(Base, unittest.TestCase):
    url = test_url("/richtext_i18n/?_LOCALE_=ru")

    def test_render_default(self):
        self.assertTrue("Text" in browser.page_source)
        self.assertTrue(u"Формат" in browser.page_source)


class RichTextReadonlyTests(Base, unittest.TestCase):
    url = test_url("/richtext_readonly/")

    def test_render_default(self):
        self.assertEqual(findid("deformField1").text, "<p>Hi!</p>")
        self.assertEqual(findcss(".required").text, "Text")
        self.assertEqual(findid("captured").text, "None")


class UnicodeEverywhereTests(Base, unittest.TestCase):
    url = test_url("/unicodeeverywhere/")

    def test_render_default(self):
        description = u"子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？ " u"人不知而不慍，不亦君子乎？」"

        self.assertTrue(u"По оживлённым берегам" in browser.page_source)
        self.assertEqual(findcss(".help-block").text, description)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "field"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), u"☃"
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit(self):
        findid("deformsubmit").click()
        self.assertRaises(NoSuchElementException, findcss, ".has-error")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), u"☃"
        )
        captured = findid("captured").text
        self.assertTrue(
            captured
            in (
                "{'field': '\\xe2\\x98\\x83'}",
                "{'field': '\u2603'}",
            ),  # py2  # py3
            captured,
        )


class SequenceOfSequencesTests(Base, unittest.TestCase):
    url = test_url("/sequence_of_sequences/")

    def test_render_default(self):
        self.assertEqual(
            findid("deformField1-addtext").text, "Add Names and Titles"
        )
        self.assertEqual(
            findid("deformField6-addtext").text, "Add Name and Title"
        )
        self.assertEqual(findid("deformField21").text, "")
        self.assertEqual(findid("deformField22").text, "")
        self.assertEqual(findid("captured").text, "None")

    def test_add_two(self):
        findid("deformField1-seqAdd").click()
        findid("deformField6-seqAdd").click()
        findxpaths('//input[@name="name"]')[0].send_keys("name")
        findxpaths('//input[@name="title"]')[0].send_keys("title")
        findxpaths('//input[@name="name"]')[1].send_keys("name")
        findxpaths('//input[@name="title"]')[1].send_keys("title")
        findxpaths('//input[@name="name"]')[2].send_keys("name")
        findxpaths('//input[@name="title"]')[2].send_keys("title")
        findid("deformsubmit").click()
        self.assertEqual(
            eval(findid("captured").text),
            {
                "names_and_titles_sequence": [
                    [
                        {"name": "name", "title": "title"},
                        {"name": "name", "title": "title"},
                    ],
                    [{"name": "name", "title": "title"}],
                ]
            },
        )

    def test_remove_from_nested_mapping_sequence(self):
        findid("deformField1-seqAdd").click()
        self.assertEqual(len(findxpaths('//input[@name="name"]')), 2)
        findcsses(".deform-close-button")[3].click()
        self.assertEqual(len(findxpaths('//input[@name="name"]')), 1)


class SequenceOrderableTests(Base, unittest.TestCase):
    url = test_url("/sequence_orderable/")

    def test_render_default(self):
        self.assertTrue(findcss(".deform-proto"))
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(findid("deformField1-addtext").text, "Add Person")

    def test_submit_complex_interaction(self):
        action_chains_on_id("deformField1-seqAdd").click().perform()

        # A single item shouldn't have an active reorder button.
        self.assertEqual(len(findcsses(".deform-order-button")), 1)
        self.assertFalse(findcsses(".deform-order-button")[0].is_displayed())

        # add a second
        action_chains_on_id("deformField1-seqAdd").click().perform()
        # Now there should be 2 active reorder buttons.
        self.assertEqual(len(findcsses(".deform-order-button")), 2)

        # add a third
        action_chains_on_id("deformField1-seqAdd").click().perform()
        time.sleep(2)
        input_ages = browser.find_elements_by_xpath('//input[@name="age"]')
        input_names = browser.find_elements_by_xpath('//input[@name="name"]')

        ActionChains(browser).move_to_element(
            input_names[0]
        ).click().send_keys("Name1").perform()
        ActionChains(browser).move_to_element(input_ages[0]).click().send_keys(
            "11"
        ).perform()

        ActionChains(browser).move_to_element(
            input_names[1]
        ).click().send_keys("Name2").perform()
        ActionChains(browser).move_to_element(input_ages[1]).click().send_keys(
            "22"
        ).perform()

        ActionChains(browser).move_to_element(
            input_names[2]
        ).click().send_keys("Name3").perform()
        ActionChains(browser).move_to_element(input_ages[2]).click().send_keys(
            "33"
        ).perform()

        seq_height = findcss(".deform-seq-item").size["height"]

        persons = browser.find_elements_by_xpath(
            '//div[@class="panel-heading"][contains(text(), "Person")]'
        )

        # Move item 3 up two
        ActionChains(browser).drag_and_drop_by_offset(
            persons[2], 0, -seq_height * 2.5
        ).perform()

        # Move item 1 down one slot (actually a little more than 1 is
        # needed to trigger jQuery Sortable when dragging down, so use 1.5).
        ActionChains(browser).drag_and_drop_by_offset(
            persons[0], 0, seq_height * 1.5
        ).perform()

        findid("deformsubmit").click()

        # sequences should be in reversed order
        inputs = findxpaths('//input[@name="name"]')
        self.assertEqual(inputs[0].get_attribute("value"), "Name3")
        self.assertEqual(inputs[1].get_attribute("value"), "Name2")
        self.assertEqual(inputs[2].get_attribute("value"), "Name1")

        self.assertEqual(
            eval(findid("captured").text),
            {
                "people": [
                    {"name": "Name3", "age": 33},
                    {"name": "Name2", "age": 22},
                    {"name": "Name1", "age": 11},
                ]
            },
        )


class TextAreaCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textareacsv/")

    def test_render_default(self):
        self.assertTrue("Csv" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "csv"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("rows"), "10"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("cols"), "60"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"),
            "1,hello,4.5\n2,goodbye,5.5\n",
        )
        self.assertEqual(findcss(".required").text, "Csv")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_default(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {
                "csv": [
                    (1, "hello", Decimal("4.5")),
                    (2, "goodbye", Decimal("5.5")),
                ]
            },
        )

    def test_submit_line_error(self):
        findid("deformField1").clear()
        findid("deformField1").send_keys("1,2,3\nwrong")
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("captured").text, "None")
        self.assertTrue(
            "has an incorrect number of elements (expected 3, was 1)"
            in findid("error-deformField1").text
        )

    def test_submit_empty(self):
        findid("deformField1").clear()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")


class WidgetAdapterTests(TextAreaCSVWidgetTests):
    url = test_url("/widget_adapter/")


class TextInputCSVWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinputcsv/")

    def test_render_default(self):
        self.assertTrue("Csv" in browser.page_source)
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "1,hello,4.5"
        )
        self.assertEqual(findcss(".required").text, "Csv")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_default(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {"csv": (1, "hello", Decimal("4.5"))},
        )

    def test_submit_line_error(self):
        findid("deformField1").clear()
        findid("deformField1").send_keys("1,2,wrong")
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("captured").text, "None")
        self.assertTrue(
            '"wrong" is not a number' in findid("error-deformField1").text
        )

    def test_submit_empty(self):
        findid("deformField1").clear()
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("captured").text, "None")


class MultipleFormsTests(Base, unittest.TestCase):
    url = test_url("/multiple_forms/")

    def test_render_default(self):
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "name1"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField3").get_attribute("name"), "name2")
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_first(self):
        findid("deformField1").send_keys("hey")
        findid("form1submit").click()
        self.assertEqual(eval(findid("captured").text), {"name1": "hey"})

    def test_submit_second(self):
        findid("deformField3").send_keys("hey")
        findid("form2submit").click()
        self.assertEqual(eval(findid("captured").text), {"name2": "hey"})


class RequireOneFieldOrAnotherTests(Base, unittest.TestCase):
    url = test_url("/require_one_or_another/")

    def test_render_default(self):
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "one"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "")
        self.assertEqual(findid("deformField2").get_attribute("name"), "two")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_submit_none_filled(self):
        wait_to_click("#deformsubmit")
        self.assertEqual(
            findid("error-deformField1").text,
            "Required if two is not supplied",
        )
        self.assertEqual(
            findid("error-deformField2").text,
            "Required if one is not supplied",
        )
        self.assertEqual(findid("captured").text, "None")

    def test_submit_one_filled(self):
        findid("deformField1").send_keys("one")
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text), {"one": "one", "two": ""}
        )
        self.assertRaises(NoSuchElementException, findcss, ".has-error")


class AjaxFormTests(Base, unittest.TestCase):
    url = test_url("/ajaxform/")

    def test_render_default(self):
        self.assertEqual(findid("captured").text, "None")
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField3").get_attribute("value"), "")
        self.assertEqual(findid("deformField4").get_attribute("value"), "")
        self.assertEqual(
            findid("deformField4-month").get_attribute("value"), ""
        )
        self.assertEqual(findid("deformField4-day").get_attribute("value"), "")

    def test_submit_empty(self):
        source = browser.page_source
        wait_to_click("#deformsubmit")
        wait_for_ajax(source)
        self.assertEqual(findid("error-deformField1").text, "Required")
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_invalid(self):
        findid("deformField1").send_keys("notanumber")
        source = browser.page_source
        wait_to_click("#deformsubmit")
        wait_for_ajax(source)
        self.assertEqual(
            findid("error-deformField1").text, '"notanumber" is not a number'
        )
        self.assertEqual(findid("error-deformField3").text, "Required")
        self.assertEqual(findid("error-deformField4").text, "Required")
        self.assertEqual(findid("captured").text, "None")

    def test_submit_success(self):
        findid("deformField1").send_keys("1")
        findid("deformField3").send_keys("name")
        findid("deformField4").send_keys("2010")
        findid("deformField4-month").send_keys("1")
        findid("deformField4-day").send_keys("1")
        browser.switch_to.frame(browser.find_element_by_tag_name("iframe"))
        findid("tinymce").send_keys("yo")
        browser.switch_to.default_content()
        source = browser.page_source
        wait_to_click("#deformsubmit")
        wait_for_ajax(source)
        self.assertEqual(findid("thanks").text, "Thanks!")


class RedirectingAjaxFormTests(AjaxFormTests):
    url = test_url("/ajaxform_redirect/")

    def test_submit_success(self):
        action_chains_on_id("deformField1").click().send_keys("1").perform()
        action_chains_on_id("deformField3").click().send_keys("name").perform()
        action_chains_on_id("deformField4").click().send_keys("2010").perform()
        action_chains_on_id("deformField4-month").click().send_keys(
            "1"
        ).perform()
        action_chains_on_id("deformField4-day").click().send_keys(
            "1"
        ).perform()
        source = browser.page_source
        wait_to_click("#deformsubmit")
        wait_for_ajax(source)
        WebDriverWait(browser, 10).until(EC.url_contains("thanks.html"))
        self.assertTrue(browser.current_url.endswith("thanks.html"))


class TextInputMaskTests(Base, unittest.TestCase):
    url = test_url("/text_input_masks/")

    def test_render_default(self):
        action_chains_on_id("deformField1").send_keys(Keys.HOME).send_keys(
            "0"
        ).perform()
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "0__-__-____"
        )
        self.assertEqual(
            findid_view("deformField1").get_attribute("name"), "ssn"
        )
        self.assertEqual(findid("deformField2").get_attribute("value"), "")
        self.assertEqual(findid("deformField2").get_attribute("name"), "date")
        self.assertRaises(NoSuchElementException, findcss, ".has-error")

    def test_type_bad_input(self):
        action_chains_on_id("deformField1").send_keys(Keys.HOME).send_keys(
            "0a"
        ).perform()
        self.assertEqual(
            findid_view("deformField1").get_attribute("value"), "0__-__-____"
        )
        action_chains_on_id("deformField2").click().send_keys(
            Keys.HOME
        ).send_keys("0a").perform()
        self.assertEqual(
            findid("deformField2").get_attribute("value"), "0_/__/____"
        )

    def test_submit_success(self):
        action_chains_on_id("deformField1").send_keys(Keys.HOME).send_keys(
            "140118866"
        ).perform()
        browser.execute_script(
            'document.getElementById("deformField2").focus();'
        )
        action_chains_on_id("deformField2").send_keys(Keys.HOME).send_keys(
            "10102010"
        ).perform()
        wait_to_click("#deformsubmit")
        self.assertEqual(
            eval(findid("captured").text),
            {"date": "10/10/2010", "ssn": "140-11-8866"},
        )


class MultipleErrorMessagesInMappingTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_mapping/")

    def test_it(self):
        findid("deformField1").send_keys("whatever")
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField1").text, "Error 1")
        self.assertEqual(findid("error-deformField1-1").text, "Error 2")
        self.assertEqual(findid("error-deformField1-2").text, "Error 3")


class MultipleErrorMessagesInSequenceTest(Base, unittest.TestCase):
    url = test_url("/multiple_error_messages_seq/")

    def test_it(self):
        findid("deformField1-seqAdd").click()
        findxpath("//input[@name='field']").send_keys("whatever")
        wait_to_click("#deformsubmit")
        self.assertEqual(findid("error-deformField3").text, "Error 1")
        self.assertEqual(findid("error-deformField3-1").text, "Error 2")
        self.assertEqual(findid("error-deformField3-2").text, "Error 3")


class CssClassesOnTheOutermostHTMLElementTests(Base, unittest.TestCase):
    url = test_url("/custom_classes_on_outermost_html_element/")

    def test_it(self):
        findcss("form > fieldset > div.top_level_mapping_widget_custom_class")
        findcss("[title=MappingWidget] div.mapped_widget_custom_class")
        findcss("[title=SequenceWidget] div.sequenced_widget_custom_class")


if __name__ == "__main__":
    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()

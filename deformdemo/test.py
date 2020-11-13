# -*- coding: utf-8 -*-
from __future__ import print_function

import ast
import logging
import os
import re
import sys
import time
import unittest

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
    """Wait until something is visible."""
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


def submit_date_picker_safe():
    """Delays caused by animation."""
    wait_to_click("#deformsubmit")


def clear_autofocused_picker():
    """
    Dismisses a date or time picker by sending an ESCAPE key.

    With the introduction of autofocus feature in Deform 3.0.0, the first field
    is assigned autofocus by default. When there is only one field that is a
    picker in the form, the pickadate by default uses the HTML5 attribute
    ``autofocus`` to trigger the display of the picker. See
    https://www.jqueryscript.net/demo/Lightweight-jQuery-Date-Input-Picker/docs.htm#api_open_close
    """
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()


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

    if driver_name == "selenium_local_chrome":

        from selenium.webdriver import Chrome

        browser = Chrome()
        return browser

    elif driver_name == "selenium_container_chrome":

        from selenium_containers import start_chrome

        from selenium.webdriver import DesiredCapabilities
        from selenium.webdriver import Remote

        start_chrome()
        time.sleep(os.getenv('WAITTOSTART', 30))

        selenium_grid_url = "http://localhost:4444/wd/hub"
        capabilities = DesiredCapabilities.CHROME.copy()

        browser = Remote(
            command_executor=selenium_grid_url,
            desired_capabilities=capabilities,
        )

        browser.set_window_size(1920, 1080)
        return browser

    elif driver_name == "selenium_container_opera":

        from selenium_containers import start_opera

        from selenium.webdriver import DesiredCapabilities
        from selenium.webdriver import Remote

        start_opera()
        time.sleep(os.getenv('WAITTOSTART', 30))

        selenium_grid_url = "http://localhost:4444/wd/hub"
        capabilities = DesiredCapabilities.OPERA.copy()

        browser = Remote(
            command_executor=selenium_grid_url,
            desired_capabilities=capabilities,
        )

        browser.set_window_size(1920, 1080)
        return browser

    elif driver_name == "selenium_container_firefox":

        from selenium_containers import start_firefox

        from selenium.webdriver import DesiredCapabilities
        from selenium.webdriver import Remote

        start_firefox()
        time.sleep(os.getenv('WAITTOSTART', 30))

        selenium_grid_url = "http://localhost:4444/wd/hub"
        capabilities = DesiredCapabilities.FIREFOX.copy()

        browser = Remote(
            command_executor=selenium_grid_url,
            desired_capabilities=capabilities,
        )

        browser.set_window_size(1920, 1080)
        return browser

    elif os.environ.get("GHA_CONTAINER_NAME") == "selenium_container_firefox":

        from selenium.webdriver import DesiredCapabilities
        from selenium.webdriver import Remote

        time.sleep(os.getenv('WAITTOSTART', 30))

        selenium_grid_url = "http://localhost:4444/wd/hub"
        capabilities = DesiredCapabilities.FIREFOX.copy()

        browser = Remote(
            command_executor=selenium_grid_url,
            desired_capabilities=capabilities,
        )

        browser.set_window_size(1920, 1080)
        return browser

    elif driver_name == "selenium_local_firefox":

        from selenium import webdriver

        try:
            browser = webdriver.Firefox()
            browser.set_window_size(1920, 1080)
        except WebDriverException:
            if os.path.exists(BROKEN_SELENIUM_LOG_FILE):
                print("Selenium says no")
                print(open(BROKEN_SELENIUM_LOG_FILE, "rt").read())
            raise
        return browser

    elif os.environ.get("DISPLAY") is not None:
        """
        Runs in Github Actions environment when WEBDRIVER or GHA_CONTAINER_NAME
        is not set, using local firefox and local geckodriver.
        https://github.com/Pylons/deform/blob/master/contributing.md
        """

        display_number = os.environ.get("DISPLAY")
        if display_number is None:

            print("ERROR: DISPLAY environment variable needs to be set.")
        else:
            print("DISPLAY is set to: {}".format(display_number))

        from selenium import webdriver

        try:
            browser = webdriver.Firefox()
            browser.set_window_size(1920, 1080)
        except WebDriverException:
            if os.path.exists(BROKEN_SELENIUM_LOG_FILE):
                print("Selenium says no")
                print(open(BROKEN_SELENIUM_LOG_FILE, "rt").read())
            raise
        return browser


def tearDownModule():
    browser.quit()
    from selenium_containers import stop_selenium_containers

    stop_selenium_containers()


def _getFile(name="test.py"):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    filename = os.path.split(path)[-1]
    return path, filename


# appease pytest by giving a default argument, it thinks this is a test
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


class TextInputWidgetTests(Base, unittest.TestCase):
    url = test_url("/textinput/")

    def test_submit_filled(self):
        findid("deformField1").send_keys("hello")
        findid("deformsubmit").click()
        element = findid("deformField1")
        self.assertRaises(NoSuchElementException, findcss, ".is-invalid")
        self.assertEqual(element.get_attribute("value"), "hello")
        captured = findid("captured").text
        self.assertSimilarRepr(captured, "{'text': u'hello'}")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings(
        action="ignore", message="unclosed", category=ResourceWarning
    )

    setUpModule()
    try:
        unittest.main()
    finally:
        tearDownModule()

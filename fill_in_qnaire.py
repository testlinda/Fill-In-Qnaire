import os
from selenium import webdriver
import socket
import argparse
import time
from datetime import datetime


class ArgConfig:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-qnaire_id", dest="qnaire_id", type=str,
                            help='qnaire id')
        parser.add_argument("-option", dest="option", type=int, default=0,
                            help='0: clock on, 1: clock off')
        self.args = parser.parse_args()
        self.qnaire_id = self.args.qnaire_id
        self.option = self.args.option


class FillInQnaire:
    def __init__(self, webdriver):
        self.webdriver = webdriver
        self.qnaire_id = ""
        self.username = ""
        self.password = ""
        self.delay = 3
        self.loginOK = False
        self.maxRetryTime = 3

    def setCredential(self, username, password):
        self.username = username
        self.password = password

    def setConfig(self, delay):
        self.delay = delay

    def gotoPage(self, link_prefix, qnaire_id):
        assert link_prefix != "", 'link_prefix should not be empty string'
        assert qnaire_id != "", 'qnaire_id should not be empty string'
        self.qnaire_id = qnaire_id
        self.webdriver.get(link_prefix + self.qnaire_id)

    def login(self):
        assert self.username != "", 'username should not be empty string'
        assert self.password != "", 'password should not be empty string'

        tryResult = self.tryLoadPage()
        assert tryResult, "Load page failed (Login)"

        try:
            self.webdriver.find_element_by_name('name').send_keys(self.username)
            self.webdriver.find_element_by_name('pass').send_keys(self.password)
            self.webdriver.find_element_by_name('op').click()
            self.loginOK = True
        except Exception as ex:
            assert False, "Login failed (%s): %s" % (self.qnaire_id, str(ex))

        self.slowdown()

    def do3949(self):
        assert self.loginOK, 'You should login first'

        tryResult = self.tryLoadPage()
        assert tryResult, "Page loaded failed (%s)" % self.qnaire_id

        try:
            self.webdriver.find_element_by_id("edit-submitted-work-area-1").click()

            option_no1 = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'無')]]")
            for element in option_no1:
                self.webdriver.execute_script("arguments[0].click();", element)

            option_no2 = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'否/')]]")
            for element in option_no2:
                self.webdriver.execute_script("arguments[0].click();", element)

            self.webdriver.find_element_by_name('op').click()

        except Exception as ex:
            assert False, "Fill in data failed (%s): %s" % (self.qnaire_id, str(ex))

        self.slowdown()

    def do4169(self, option):
        assert self.loginOK, 'You should login first'

        tryResult = self.tryLoadPage()
        assert tryResult, "Page loaded failed (%s)" % self.qnaire_id

        tasks = "Software development\nBug fixing remotely"

        try:
            if option == 0:
                elements = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'上班')]]")
                for element in elements:
                    self.webdriver.execute_script("arguments[0].click();", element)
            elif option == 1:
                elements = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'下班')]]")
                for element in elements:
                    self.webdriver.execute_script("arguments[0].click();", element)

                self.webdriver.find_element_by_id('edit-submitted-note').send_keys(tasks)

            else:
                raise Exception("Invalid option")

            self.webdriver.find_element_by_name('op').click()

        except Exception as ex:
            assert False, "Fill in data failed (%s, option:%d): %s" \
                          % (self.qnaire_id, option, str(ex))

        self.slowdown()

    def checkSuccess(self):
        try:
            self.webdriver.find_element_by_class_name("webform-confirmation")
        except Exception as ex:
            assert False, "Failed to fill in the form (%s): %s" % (self.qnaire_id, str(ex))

    def tryLoadPage(self):
        retryTime = 0
        while retryTime < self.maxRetryTime:
            if not self.__checkPageReady():
                retryTime += 1
                self.__retry(retryTime)
            else:
                break

        return retryTime < self.maxRetryTime

    def slowdown(self):
        time.sleep(self.delay)

    def __checkPageReady(self):
        try:
            self.webdriver.find_element_by_name('op')
        except Exception as ex:
            return False
        return True

    def __retry(self, count):
        print("page refresh... the %d time" % count)
        self.webdriver.refresh()
        time.sleep(self.delay)


def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


def init_webdriver(is_debug=False):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    if is_debug:
        chrome_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        driver_path = 'chromedriver.exe'
        assert os.path.isfile(chrome_path), "File not exist (%s)" % chrome_path
        assert os.path.isfile(driver_path), "File not exist (%s)" % driver_path
    else:
        chrome_options.add_argument("--headless")
        chrome_path = os.environ.get("GOOGLE_CHROME_BIN")
        driver_path = os.environ.get("CHROMEDRIVER_PATH")

    chrome_options.binary_location = chrome_path
    driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

    return driver


def get_config_info(is_debug=False):
    try:
        if is_debug:
            import configparser
            parser = configparser.ConfigParser()
            parser.read("config.ini")
            username = parser.get("Setting", "username")
            password = parser.get("Setting", "password")
            delay = parser.getint("Setting", "delay")
        else:
            username = os.environ.get("APP_CONFIG_USERNAME")
            password = os.environ.get("APP_CONFIG_PASSWORD")
            delay = int(os.environ.get("APP_CONFIG_DELAY"))
    except Exception as ex:
        assert False, "Read config failed: %s" % str(ex)

    return username, password, delay


def get_qnaire_link_prefix(is_debug=False):
    try:
        if is_debug:
            import configparser
            parser = configparser.ConfigParser()
            parser.read("config.ini")
            link_prefix = parser.get("Setting", "link_prefix")
        else:
            link_prefix = os.environ.get("QNAIRE_LINK_PREFIX")
    except Exception as ex:
        assert False, "Read link prefix failed: %s" % str(ex)

    return link_prefix


def get_time():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


def main():
    print(get_time())
    args = ArgConfig()

    # debug
    args.qnaire_id = "3949"
    args.option = 1

    is_debug = False
    if os.path.isfile('config.ini'):
        is_debug = True

    while not is_connected():
        print("Internet is down, check again in 10 seconds...")
        time.sleep(10)

    try:
        driver = init_webdriver(is_debug)
        username, password, delay = get_config_info(is_debug)
        link_prefix = get_qnaire_link_prefix(is_debug)
        fiq = FillInQnaire(driver)
        fiq.setCredential(username, password)
        fiq.setConfig(delay)
        fiq.gotoPage(link_prefix, args.qnaire_id)
        fiq.login()
        if args.qnaire_id == "3949":
            fiq.do3949()
        elif args.qnaire_id == "4169":
            fiq.do4169(args.option)
        else:
            raise Exception("Invalid qnaire id")
        fiq.checkSuccess()
        print("Everything is done correctly.")
        time.sleep(1)
        driver.quit()

    except Exception as ex:
        print(str(ex))
        print("Something is wrong.")


if __name__ == '__main__':
    main()

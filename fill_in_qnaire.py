import os
from selenium import webdriver
import socket
import argparse
import time
from datetime import datetime
from get_gscript_data import GetGScriptData as gScript

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

    def do3949(self, keywords):
        assert self.loginOK, 'You should login first'

        tryResult = self.tryLoadPage()
        assert tryResult, "Page loaded failed (%s)" % self.qnaire_id

        try:
            for keyword in keywords:
                elements = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'" + keyword + "')]]")
                for element in elements:
                    self.webdriver.execute_script("arguments[0].click();", element)

            self.webdriver.find_element_by_name('op').click()

        except Exception as ex:
            assert False, "Fill in data failed (%s): %s" % (self.qnaire_id, str(ex))

        self.slowdown()

    def do4169(self, option, tasks):
        assert self.loginOK, 'You should login first'
        assert option != 1 or tasks != "", 'Task list is empty'

        tryResult = self.tryLoadPage()
        assert tryResult, "Page loaded failed (%s)" % self.qnaire_id

        try:
            if option == 0:
                elements = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'上班')]]")
                for element in elements:
                    self.webdriver.execute_script("arguments[0].click();", element)
            elif option == 1:
                elements = self.webdriver.find_elements_by_xpath("//*[text()[contains(.,'下班')]]")
                for element in elements:
                    if element.text == '下班':
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
            assert False, "Failed to check success page (%s): %s" % (self.qnaire_id, str(ex))

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


def getDebugOption():
    if not os.path.isfile('config.ini'):
        return False
    import configparser
    parser = configparser.ConfigParser()
    parser.read("config.ini")
    return parser.get("Debug", "is_debug")


def getDebugArgs():
    import configparser
    parser = configparser.ConfigParser()
    parser.read("config.ini")
    qnaire_id = parser.get("Debug", "qnaire_id")
    option = parser.getint("Debug", "option")
    return qnaire_id, option


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


def initial_gscript(is_debug=False):
    if is_debug:
        import configparser
        parser = configparser.ConfigParser()
        parser.read("config.ini")
        api_link = parser.get("Setting", "url")
    else:
        api_link = os.environ.get("GSCRIPT_API_LINK")
    return gScript(api_link)


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

    is_debug = getDebugOption()
    if is_debug:
        args.qnaire_id, args.option = getDebugArgs()

    while not is_connected():
        print("Internet is down, check again in 10 seconds...")
        time.sleep(10)

    try:
        driver = init_webdriver(is_debug)
        gscript = initial_gscript(is_debug)
        username, password, delay = gscript.getConfig()
        enabled = gscript.getEnabled(args.qnaire_id)
        link_prefix = get_qnaire_link_prefix(is_debug)
        fiq = FillInQnaire(driver)
        fiq.setCredential(username, password)
        fiq.setConfig(delay)
        fiq.gotoPage(link_prefix, args.qnaire_id)
        fiq.login()
        feedback_msg = ""

        if not enabled:
            feedback_msg = "This function is disabled."
        else:
            if args.qnaire_id == "3949":
                keywords = gscript.getKeywords3949()
                fiq.do3949(keywords)
                fiq.checkSuccess()
            elif args.qnaire_id == "4169":
                if not gscript.getHolidaybool():
                    tasks = "" if args.option == 0 else gscript.getTasks()
                    fiq.do4169(args.option, tasks)
                    fiq.checkSuccess()
                else:
                    feedback_msg = "did not fill in anything cause it's holiday >.0"

            else:
                raise Exception("Invalid qnaire id")

        print("Everything is done correctly.")
        gscript.writeLog(args.qnaire_id, "ok", feedback_msg)
        time.sleep(1)
        driver.quit()

    except Exception as ex:
        try:
            gscript.writeLog(args.qnaire_id, "not ok", str(ex))
        except:
            print("Write log failed.")

        print("Something is wrong: " + str(ex))


if __name__ == '__main__':
    main()

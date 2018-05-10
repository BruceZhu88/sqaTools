# -*- coding: utf-8 -*-
# Created on 2016.10
# @author: bruce.zhu


import os
import urllib.request
import sys
import json
import time
from src.common.Logger import Logger
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


class AseUpdate(object):
    def __init__(self, socketio, ota_setting_path):
        self.socketio = socketio
        self.log = Logger("wifi_speaker").logger()
        with open(ota_setting_path) as json_file:
            data = json.load(json_file)
            # parent_path = os.path.realpath(os.path.join(os.getcwd(), ".."))
        self.low_version_path = data["low_version_path"]
        self.high_version_path = data["high_version_path"]
        self.low_version = data["low_version"]
        self.high_version = data["high_version"]
        self.cycle = int(data["total_times"])
        self.IP = "http://" + data["ip"]
        self.title = " auto update OTA Test"

        self.shot_path = ''
        self.pageTimeout = 15
        self.update_times = 0
        self.downgrade_times = 0
        self.Network_Error = 0
        self.Run_status = ''
        # driver = webdriver.Chrome("%s\chromedriver2.9.exe"%os.getcwd())
        self.print_log("Start to Auto Update Test!")
        try:
            self.print_log("Open Setting Page by browser Firefox...")
            self.driver = webdriver.Firefox()
            self.driver.get(self.IP)
        except Exception as e:
            self.print_log(e, 'red')
            sys.exit()
            # s = unicode ("成 ", "utf-8")

    def print_log(self, info, color='white'):
        try:
            self.log.info(info)
            self.socketio.sleep(0.01)   # Avoid sockeit network block leads to cannot print on page
            self.socketio.emit('print_msg',
                               {'data': info, 'color': color},
                               namespace='/wifi_speaker/test')
        except Exception as e:
            self.log.debug("Error when print_log: {}".format(e))
            self.driver.quit()
            sys.exit()

    def screen_shot(self, info):
        self.print_log("%s\%s_%s.png" % (self.shot_path, info, time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())))
        self.driver.get_screenshot_as_file(
            "%s/%s_%s.png" % (self.shot_path, info, time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())))

    def check_network(self, url):
        try:
            # r = requests.get(url, allow_redirects = False)
            # status = r.status_code
            self.log.debug(url)
            req = urllib.request.Request(url)
            res = urllib.request.urlopen(req, timeout=8)
            status = res.status
            # r = urllib.request.urlopen(url, timeout=8)
            # status = r.getcode()
            if status == 200:
                self.print_log('Network is ok')
                return True
            else:
                self.screen_shot("Network error")
                self.log.error('Network error!!!!')
                return False
        except:
            self.screen_shot("Network error")
            self.log.error('Network error!!!!')
            return False

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    # make screen shot directory
    @staticmethod
    def make_shot_dir():
        # shot_conf = dict(root_run = os.getcwd())
        run_shot_dir = os.path.realpath(os.path.join(os.getcwd(), "./log", 'error_shot'))
        if not os.path.exists(run_shot_dir):
            os.makedirs(run_shot_dir)
        return run_shot_dir
        # shot_conf['runshot_dir'] = run_shot_dir
        # return shot_conf

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    def switch_frame(self, frame_type):
        try:
            if frame_type == "default":
                self.driver.switch_to_default_content()
            elif frame_type == "rightFrame":
                self.driver.switch_to_frame("rightFrame")
            elif frame_type == "leftFrame":
                self.driver.switch_to_frame("leftFrame")
            else:
                self.print_log("No such frame {}".format(frame_type), 'red')
        # except NotImplementedError as e:
        except Exception as e:
            self.log.error("Error when switch frame {}: {}".format(frame_type, e))
            sys.exit()
        else:
            return True

    def find_element(self, ele_type, timeout, value):
        """
        Args:
            ele_type(str): element type
            timeout(int): max time at finding element
            value(str): element attribute value
        Returns:
            ele(WebElement): return object of found element
        """
        ele = None
        try:
            if ele_type == "id":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_id(value))
                ele = self.driver.find_element_by_id(value)
            elif ele_type == "name":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_name(value))
                ele = self.driver.find_element_by_name(value)
            elif ele_type == "class_name":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_class_name(value))
                ele = self.driver.find_element_by_class_name(value)
            elif ele_type == "link_text":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_link_text(value))
                ele = self.driver.find_element_by_link_text(value)
            elif ele_type == "partial_link_text":
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.find_element_by_partial_link_text(value))
                ele = self.driver.find_element_by_partial_link_text(value)
            elif ele_type == "tag_name":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_tag_name(value))
                ele = self.driver.find_element_by_tag_name(value)
            elif ele_type == "xpath":
                WebDriverWait(self.driver, timeout).until(lambda driver: driver.find_element_by_xpath(value))
                ele = self.driver.find_element_by_xpath(value)
            else:
                self.print_log("No such locate element way {}".format(ele_type))
        except NotImplementedError as e:
            self.print_log(e, 'red')
        except TimeoutError as e:
            self.log.debug(e)
            sys.exit()
            # else:
            # return ele
        finally:
            return ele

    def update_percentage(self):
        time.sleep(20)
        while True:
            # time.sleep(8)
            if not self.check_popup():
                self.switch_frame("default")
                self.switch_frame("rightFrame")
                try:
                    confirm_update_done = self.find_element("xpath", 10, "//*[@id='ConfirmUpdateDone']")
                    confirm_update_done.click()
                    return True
                except:
                    pass
            else:
                return False

    def check_version(self, v):
        self.switch_frame("default")
        self.switch_frame("rightFrame")
        software_version = self.find_element("xpath", self.pageTimeout, "//*[@id='softwareVersion']")
        if software_version is None:
            return False
        version = software_version.text
        self.print_log("DUT current version is %s" % version)
        if v == version:
            # success_time=success_time+1
            self.print_log("Update successfully!")
            return True
        else:
            self.print_log("Update fail!", "red")
            return False

    def check_popup(self):
        """Check popup box when Uploading or updatings
        Returns:
                True: Appear popup
                False: No popup
        """
        self.switch_frame("default")
        try:
            popup = self.find_element("class_name", 1, "imgButtonYes")
            popup.is_displayed()
            # driver.find_element_by_class_name("imgButtonYes").is_displayed()
            self.screen_shot("%s_popup" % self.Network_Error)
            popup.click()
            self.print_log("Network unavailable")
            self.Network_Error += 1
            return True
        except:
            return False

    def agreement_page(self):
        time.sleep(2)
        self.switch_frame("default")
        self.switch_frame("rightFrame")
        self.log.debug('Checking if there is agreement page!')
        if self.find_element("xpath", self.pageTimeout, "//*[@id='BtnOK1']") is None:
            return False
        self.log.debug('Start to click agreement page!')
        self.find_element("xpath", self.pageTimeout, "//*[@id='BtnOK1']").click()
        time.sleep(3)
        self.find_element("xpath", self.pageTimeout, "//*[@id='BtnOK2']").click()
        time.sleep(3)
        self.switch_frame("default")
        self.switch_frame("rightFrame")
        self.find_element("xpath", self.pageTimeout, "//*[@id=\"Accept\"]").click()
        time.sleep(3)
        self.find_element("xpath", self.pageTimeout, "//*[@id='NoThanks']").click()
        time.sleep(7)
        return True

    def update_local(self, local_file):
        self.log.debug("Ready to uploade on local")
        self.switch_frame("default")
        self.switch_frame("rightFrame")
        time.sleep(1)

        self.log.debug("Click LocalUpdateButton")
        local_update_button = self.find_element("xpath", self.pageTimeout, "//*[@id='LocalUpdateButton']")
        local_update_button.click()
        time.sleep(2)

        datafile = self.find_element("xpath", self.pageTimeout, "//*[@id='datafile']")
        try:
            datafile.send_keys('%s' % local_file)
        except Exception as e:
            self.log.debug(e)
            sys.exit()
        time.sleep(3)

        loadfile_button = self.find_element("xpath", self.pageTimeout, "//*[@id='LoadFileButton']")
        loadfile_button.click()

        self.print_log("Uploading %s file..." % local_file)
        while True:
            time.sleep(5)
            if self.check_popup():
                return False
            self.switch_frame("rightFrame")
            try:
                confirm_yes = self.find_element("xpath", self.pageTimeout, "//*[@id='LocalUpdateConfirmYes']")
                confirm_yes.click()
                self.print_log("Uploading success!")
                self.print_log("Start burn into...!")
                if not self.update_percentage():
                    return False
                else:
                    return True
            except:
                self.log.debug('Wait for Yes button')

    def update_server(self, current_version):
        local_file = self.low_version_path
        if current_version == self.high_version:
            self.print_log("Downgrade from local")
            if not self.update_local(local_file):
                return False
            time.sleep(10)
            if self.check_version(self.low_version):
                self.print_log(
                    "Downgrade successfully from %s to version %s on local" % (self.high_version, self.low_version))
                self.downgrade_times += 1
                return True
        else:
            self.print_log("Update from server")
            time.sleep(2)
            self.switch_frame("default")
            self.switch_frame("rightFrame")
            time.sleep(10)
            try:
                new_sw_version = self.find_element("xpath", self.pageTimeout, "//*[@id='NewSWVersion']")
            except:
                return False    # Cannot check new version
            if new_sw_version.text == self.high_version:
                update_from_network_button = self.find_element("xpath", self.pageTimeout,
                                                               "//*[@id='UpdateFromNetworkButton']")
                update_from_network_button.click()
                time.sleep(3)
                network_update_confirm_yes = self.find_element("xpath", self.pageTimeout,
                                                               "//*[@id='NetworkUpdateConfirmYes']")
                network_update_confirm_yes.click()
                self.print_log("Start update!")
            if not self.update_percentage():
                return False
            time.sleep(10)
            if self.check_version(self.high_version):
                self.print_log(
                    "Update successfully from %s to version %s on internet" % (self.low_version, self.high_version))
                self.update_times += 1
                return True

    def update_full(self):
        try:
            self.print_log(self.driver.title + "(" + self.IP + ")")
        except Exception as e:
            self.print_log(e, 'red')
            sys.exit()
        for i in range(0, 15):
            try:
                if self.agreement_page():
                    break
                else:
                    self.switch_frame("default")
                    self.switch_frame("rightFrame")
                    if self.find_element("xpath", self.pageTimeout, "//*[@id='softwareVersion']") is not None:
                        break
            except:
                continue
        time.sleep(2)
        self.switch_frame("default")
        self.switch_frame("rightFrame")
        current_version = self.find_element("xpath", self.pageTimeout, "//*[@id='softwareVersion']").text

        self.print_log("DUT current version is %s" % current_version)
        self.switch_frame("default")

        time.sleep(2)
        self.switch_frame("leftFrame")
        sw_update_page = self.find_element("xpath", self.pageTimeout, "//*[@id='SwUpdatePage']/span")
        sw_update_page.click()
        time.sleep(3)  # wait page
        # if current version is not high or low version, force updating to high version
        if (current_version != self.low_version) and (current_version != self.high_version):
            self.update_local(self.high_version_path)
            time.sleep(10)
            self.check_version(self.high_version)
            return True

        # Update from server
        if self.low_version_path == self.high_version_path:
            if not self.update_server(current_version):
                return False
            return True

        # Update from local
        else:
            if current_version == self.high_version:
                local_file = self.low_version_path
                version_check = self.low_version
                self.print_log("Downgrade to version %s just with local file" % version_check)
            else:
                local_file = self.high_version_path
                version_check = self.high_version
                self.print_log("Update to version %s just with local file" % version_check)

            if not self.update_local(local_file):
                return False
            time.sleep(10)
            if self.check_version(version_check):
                if version_check == self.low_version:
                    self.print_log(
                        "Downgrade successfully from %s to version %s on local" % (self.high_version, self.low_version))
                    self.downgrade_times += 1
                elif version_check == self.high_version:
                    self.print_log(
                        "Update successfully from %s to version %s on local" % (self.low_version, self.high_version))
                    self.update_times += 1
                else:
                    self.print_log("No such version! Error", 'red')
                    return False
            return True

    def start_ota(self):
        self.Run_status = "Running"
        self.shot_path = self.make_shot_dir()
        # start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        # start = time.time()

        for i in range(1, self.cycle + 1):
            self.print_log("This is %i times----------------------------------------" % i)
            for j in range(0, 2):
                if self.check_network(self.IP + "/index.fcgi"):
                    # when version file have been download from server(on updating),but the net disconnect
                    if not self.update_full():
                        self.print_log("Maybe Network trouble, so wait 100 second, then open setting page again")
                        time.sleep(100)  # why is 100s, as sometimes, update still can go on by DUT self
                        self.driver.quit()
                        # self.driver = webdriver.Chrome("%s\chromedriver.exe" % os.getcwd())
                        self.driver = webdriver.Firefox()
                        self.driver.get(self.IP)
                    if i == self.cycle:
                        self.Run_status = "Running Over"
                    # end = time.time()
                    # diff_time = int(end-start)
                    # duration="%sh:%sm:%ss"%(int((end-start)/3600),int((end-start)/60),int((end-start)%60))
                    # duration = str(datetime.timedelta(seconds=int(time.time() - start)))
                    # self.print_log("Success update times is %d"%self.update_times)
                    self.socketio.emit('refresh_update_status',
                                       {"network_error": self.Network_Error,
                                        "pass_upgrade": '{0}/{1} (Upgrade)'.format(self.update_times, i),
                                        "pass_downgrade": '{0}/{1} (Downgrade)'.format(self.downgrade_times, i)},
                                       namespace='/wifi_speaker/test')
                    # CreateHTMLRpt.report_result(self.title,start_time,duration,str(i),self.Run_status,update,str(self.update_times),downgrade,str(self.downgrade_times),'self.Network_Error',str(self.Network_Error))

        self.driver.quit()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Main()
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
if __name__ == '__main__':
    update = AseUpdate()
    update.start_ota()

import re
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class FacebookChrome:
    def __init__(self, username, password, key_2fa=None, proxy=None, tag_uids=[]):
        self.options = Options()
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument('--deny-permission-prompts')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument(
            "--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("useAutomationExtension", False)
        self.options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])
        self.options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile': {
                'password_manager_enabled': False
            }
        })
        self.options.add_experimental_option(
            'excludeSwitches', ['disable-popup-blocking'])
        
        self.options.add_argument('--headless')
        
        # if headless:
        #     self.options.add_argument('--headless')
        # if not enable_images:
        #     self.options.add_argument('--blink-settings=imagesEnabled=false')
        #     prefs = {"profile.managed_default_content_settings.images": 2}
        #     self.options.add_experimental_option("prefs", prefs)
        # if not enable_css:
        #     self.options.add_experimental_option(
        #         "prefs", {"profile.managed_default_content_settings.stylesheets": 2})
        #     self.options.set_capability(
        #         'goog:loggingPrefs', {'browser': 'ALL'})
        # if proxy:
        #     self.options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get('https://mbasic.facebook.com')
        cookie = {
            'name': 'locale',
            'value': 'en_GB'
        }
        self.driver.add_cookie(cookie)
        self.username = username
        self.password = password
        self.key_2fa = key_2fa
        self.tag_uids = tag_uids

    def login(self):
        """
        ---
        Đăng nhập vào Facebook
        ---
        ### Các tham số:
            - username (str): Tên người Facebook.
            - password (str): Mật khẩu Facebook
            - key_2fa (str): KEY 2FA để lấy mã xác thực.
        ---
        ### Trả về:
            - str: "SUCCESS" nếu đăng nhập thành công, "FAILED" nếu sai pass hoặc sai 2FA
        """
        self.driver.get('https://mbasic.facebook.com')
        username_input = self.driver.find_element(By.ID, 'm_login_email')
        username_input.clear()
        username_input.send_keys(self.username)
        password_input = self.driver.find_element(By.NAME, 'pass')
        password_input.clear()
        password_input.send_keys(self.password)
        login_button = self.driver.find_element(By.NAME, 'login')
        login_button.click()
        if 'https://mbasic.facebook.com/login/' in self.driver.current_url:
            return "FAILED"
        if 'https://mbasic.facebook.com/checkpoint/?_rdr' in self.driver.current_url:
            code_2fa = self._get_code_2fa(self.key_2fa)
            code_2fa_input = self.driver.find_element(
                By.NAME, 'approvals_code')
            code_2fa_input.clear()
            code_2fa_input.send_keys(code_2fa)
            submit_button = self.driver.find_element(
                By.NAME, 'submit[Submit Code]')
            submit_button.click()
            if 'https://mbasic.facebook.com/login/checkpoint/' in self.driver.current_url:
                for i in range(10):
                    if i == 9:
                        return "FAILED"
                    try:
                        this_was_me_button = self.driver.find_element(
                            By.NAME, 'submit[This was me]')
                        this_was_me_button.click()
                    except:
                        pass
                    time.sleep(1)
                    submit_button = self.driver.find_element(
                        By.NAME, 'submit[Continue]')
                    submit_button.click()
                    if 'https://mbasic.facebook.com/login/checkpoint/' not in self.driver.current_url:
                        break
        return "SUCCESS"
    
    def change_avatar(self, image_path):
        if not image_path:
            return "Can not upload image"
        
        uid = self._get_uid()
        self.driver.get(f'https://mbasic.facebook.com/{uid}')
        image_button = self.driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div[1]/div[2]/div/div[2]/a')
        image_button.click()
        image_input = self.driver.find_element(By.NAME, f'file1')
        image_input.send_keys(image_path)
        post_button = self.driver.find_element(By.XPATH, '//*[@id="root"]/table/tbody/tr/td/div/form/div[2]/input')
        post_button.click()
        time.sleep(2)
        self.driver.get("https://mbasic.facebook.com")

    def post_status(self, message: str):
        for tag_uid in self.tag_uids:
            message += f"@[{tag_uid}:0]"    

        uid = self._get_uid()
        self.driver.get(f'https://mbasic.facebook.com/{uid}')
        view_more = self.driver.find_element(By.NAME, 'view_overview')
        view_more.click()
        text_area = self.driver.find_element(By.NAME, 'xc_message')
        text_area.send_keys(message)
        post_button = self.driver.find_element(By.NAME, 'view_post')
        post_button.click()
        return "SUCCESS"


    def _get_code_2fa(self, key_2fa: str):
        url = f"https://2fa.live/tok/{key_2fa}"
        response = requests.get(url)
        data = response.json()
        return data.get("token")
    
    def _get_uid(self):
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "c_user":
                uid = cookie["value"]
                break

        if not uid:
            raise ValueError("Không thể lấy UID từ cookie.")
        return uid


# 7qebfjijjl@txcct.com|risadia15|OG2K3RWCCHPIYACEPREGEKV7YL5OIYVZ|
import os
import random
import signal
from typing import Dict, List, Optional

import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class FacebookChrome:
    def __init__(self, cookies: str, proxy: Optional[str] = None):
        self.options = Options()
        self.base_url = 'https://mbasic.facebook.com'
        # self.options.add_argument('--headless')
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
        if proxy:
            self.options.add_argument(f"--proxy-server={proxy}")

        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(self.base_url)
        self.cookies = cookies
        self.pid = self._get_pid()

    def _get_pid(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'chrome.exe':
                    if 'webdriver' in proc.cmdline():
                        return proc.info['pid']
        except Exception as e:
            print(f"Error getting PID: {e}")
        return None

    def _get_uid(self) -> Optional[str]:
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "c_user":
                return cookie["value"]
        self.driver.quit()
        return None

    def _gen_random_number(self) -> str:
        return ''.join(random.choices('0123456789', k=6))

    def _parse_cookies(self, cookies_str: str) -> List[Dict[str, str]]:
        cookies = []
        for cookie in cookies_str.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                cookies.append({'name': name.strip(), 'value': value.strip()})
        return cookies

    def login(self) -> str:
        LOGIN_ERROR_MESSAGE = "LỖI ĐĂNG NHẬP"
        try:
            cookies = self._parse_cookies(self.cookies)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.get(self.base_url)
            feed_compose = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.ID, 'mbasic_inline_feed_composer'))
            )
            if feed_compose:
                return "ĐĂNG NHẬP THÀNH CÔNG"
            else:
                return LOGIN_ERROR_MESSAGE
        except Exception:
            return "LỖI ĐĂNG NHẬP COOKIE. CHECK COOKIE LẠI"

    def change_avatar(self, image_path: str) -> str:
        if not image_path:
            return "LỖI: KHÔNG CUNG CẤP ẢNH"
        uid = self._get_uid()
        if not uid:
            return "LỖI: KHÔNG TÌM THẤY UID"
        self.driver.get(f'{self.base_url}/{uid}')
        try:
            image_button = self.driver.find_element(
                By.XPATH, '//*[@id="root"]/div[1]/div[1]/div[2]/div/div[2]/a')
            image_button.click()
            image_input = self.driver.find_element(By.NAME, 'file1')
            image_input.send_keys(image_path)
            post_button = self.driver.find_element(
                By.XPATH, '//*[@id="root"]/table/tbody/tr/td/div/form/div[2]/input')
            post_button.click()
            self.driver.get(f'{self.base_url}/{uid}')
            avatar_element = self.driver.find_element(
                By.XPATH, '//img[contains(@src, "https://scontent.") and contains(@class, "bt") and contains(@class, "img")]')
            avatar_element.click()
            privacy_buton = self.driver.find_element(
                By.XPATH, '//a[contains(@href, "/privacyx/selector")]')
            privacy_buton.click()
            see_more_button = self.driver.find_element(
                By.XPATH, '//a[contains(@href, "/privacyx/selector")]'
            )
            see_more_button.click()
            only_me_button = self.driver.find_element(
                By.CSS_SELECTOR, 'a[aria-label="Only me"]')
            only_me_button.click()
            return "ĐỔI AVATAR THÀNH CÔNG"
        except Exception as e:
            print(f"Lỗi: {e}")
            return "LỖI ĐỔI AVATAR KHÔNG THÀNH CÔNG"

    def post_status(self, message: str, uids: List[str]) -> str:
        if not uids:
            return "LỖI: KHÔNG CUNG CẤP UID"

        uid = self._get_uid()
        if not uid:
            return "LỖI: KHÔNG TÌM THẤY UID"

        for uid_ in uids:
            message = message + "\n" + f"@[{uid_[0]}:0]"

        message = message + "\n" + f"#{self._gen_random_number()}"

        self.driver.get(f'{self.base_url}/{uid}')
        try:
            view_more = self.driver.find_element(By.NAME, 'view_overview')
            view_more.click()
            privacy_element = self.driver.find_element(By.NAME, 'view_privacy')
            privacy_element.click()
            self.driver.execute_script(
                "document.getElementById('300645083384735').click();")
            self.driver.execute_script(
                "document.getElementById('m_composer_set_as_default_privacy_selector').click();")
            self.driver.execute_script(
                "document.querySelector('input[type=\"submit\"]').click();")
            text_area = self.driver.find_element(By.NAME, 'xc_message')
            text_area.send_keys(message)
            post_button = self.driver.find_element(By.NAME, 'view_post')
            post_button.click()
            try:
                links = self.driver.find_elements(
                    By.CSS_SELECTOR, 'a[href*="/story.php"]')
                if links:
                    latest_link = links[0]
                    latest_url = latest_link.get_attribute('href')

                    def get_param_from_url(url, param):
                        from urllib.parse import parse_qs, urlparse
                        parsed_url = urlparse(url)
                        params = parse_qs(parsed_url.query)
                        return params.get(param, [None])[0]

                    story_fbid = get_param_from_url(latest_url, 'story_fbid')
                    post_id = get_param_from_url(latest_url, 'id')
                    if story_fbid and post_id:
                        new_url = f"https://en-gb.facebook.com/permalink.php?story_fbid={story_fbid}&id={post_id}"
                        self.driver.get(new_url)
                        edit_button = self.driver.find_element(
                            By.XPATH, '//div[@aria-label="Actions for this post"]')
                        edit_button.click()
                        edit_post_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, '//span[text()="Edit post"]/parent::div/parent::div'))
                        )
                        edit_post_button.click()
                        remove_link_preview_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, '//div[@aria-label="Remove link preview from your post"]'))
                        )
                        remove_link_preview_button.click()
                        WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 '//div[@aria-label="Remove link preview from your post"]')
                            )
                        )

                        remove_link_preview_button.click()
                        save_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, '//div[@aria-label="Save"]'))
                        )
                        save_button.click()
            except Exception as e:
                print(f"Lỗi: {e}")
                return "ĐĂNG TRẠNG THÁI THÀNH CÔNG"

            return "ĐĂNG TRẠNG THÁI THÀNH CÔNG"
        except Exception as e:
            print(f"Lỗi: {e}")
            return "LỖI ĐĂNG TRẠNG THÁI KHÔNG THÀNH CÔNG"

    def quit(self) -> str:
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except Exception as e:
                print(f"Error killing process: {e}")
        self.driver.quit()
        return "ĐÃ DỪNG LẠI"

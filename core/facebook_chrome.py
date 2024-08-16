import random
from typing import Dict, List, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class FacebookChrome:
    def __init__(self, username: str, password: str, cookies: str, key_2fa: Optional[str] = None, proxy: Optional[str] = None):
        self.options = Options()
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
        self.driver.get('https://mbasic.facebook.com')
        cookie = {'name': 'locale', 'value': 'en_GB'}
        self.driver.add_cookie(cookie)
        self.username = username
        self.password = password
        self.key_2fa = key_2fa
        self.cookies = cookies

    def _get_code_2fa(self, key_2fa: str) -> Optional[str]:
        url = f"https://2fa.live/tok/{key_2fa}"
        response = requests.get(url)
        data = response.json()
        return data.get("token")

    def _get_uid(self) -> Optional[str]:
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "c_user":
                return cookie["value"]
        self.driver.quit()
        return None

    def get_cookies(self) -> Dict[str, str]:
        cookies = self.driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def login(self, login_with_proxy: bool = False) -> str:
        LOGIN_ERROR_MESSAGE = "LỖI ĐĂNG NHẬP"
        if login_with_proxy:
            try:
                cookies = self.cookies.split(";")
                for cookie in cookies:
                    name, value = cookie.split("=")
                    self.driver.add_cookie({'name': name.strip(), 'value': value.strip()})
                
                self.driver.get('https://mbasic.facebook.com')

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
        else:
            try:
                self.driver.get('https://mbasic.facebook.com')
                username_input = self.driver.find_element(By.ID, 'm_login_email')
                username_input.clear()
                username_input.send_keys(self.username)
                password_input = self.driver.find_element(By.NAME, 'pass')
                password_input.clear()
                password_input.send_keys(self.password)
                login_button = self.driver.find_element(By.NAME, 'login')
                login_button.click()
            except:
                return LOGIN_ERROR_MESSAGE
            if 'https://mbasic.facebook.com/login/' in self.driver.current_url:
                self.driver.quit()
                return LOGIN_ERROR_MESSAGE
            if 'https://mbasic.facebook.com/checkpoint/?_rdr' in self.driver.current_url:
                code_2fa = self._get_code_2fa(self.key_2fa or '')
                code_2fa_input = self.driver.find_element(
                    By.NAME, 'approvals_code')
                code_2fa_input.clear()
                code_2fa_input.send_keys(code_2fa)
                try:
                    submit_button = self.driver.find_element(
                        By.NAME, 'submit[Submit Code]')
                except:
                    return LOGIN_ERROR_MESSAGE
                submit_button.click()
                if 'https://mbasic.facebook.com/login/checkpoint/' in self.driver.current_url:
                    for i in range(10):
                        if i == 9:
                            self.driver.quit()
                            return LOGIN_ERROR_MESSAGE
                        try:
                            this_was_me_button = self.driver.find_element(
                                By.NAME, 'submit[This was me]')
                            this_was_me_button.click()
                        except:
                            pass
                        try:
                            submit_button = self.driver.find_element(
                                By.NAME, 'submit[Continue]')
                        except:
                            return LOGIN_ERROR_MESSAGE
                        submit_button.click()
                        if 'https://mbasic.facebook.com/login/checkpoint/' not in self.driver.current_url:
                            break
            return "ĐĂNG NHẬP THÀNH CÔNG"

    def change_avatar(self, image_path: str) -> str:
        if not image_path:
            return "LỖI: KHÔNG CUNG CẤP ẢNH"
        uid = self._get_uid()
        if not uid:
            return "LỖI: KHÔNG TÌM THẤY UID"
        self.driver.get(f'https://mbasic.facebook.com/{uid}')
        try:
            image_button = self.driver.find_element(
                By.XPATH, '//*[@id="root"]/div[1]/div[1]/div[2]/div/div[2]/a')
            image_button.click()
            image_input = self.driver.find_element(By.NAME, 'file1')
            image_input.send_keys(image_path)
            post_button = self.driver.find_element(
                By.XPATH, '//*[@id="root"]/table/tbody/tr/td/div/form/div[2]/input')
            post_button.click()
            self.driver.get(f'https://mbasic.facebook.com/{uid}')
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
        except:
            return "LỖI ĐỔI AVATAR KHÔNG THÀNH CÔNG"

    def post_status(self, message: str, uids: List[str]) -> str:
        if not uids:
            return "LỖI: KHÔNG CUNG CẤP UID"

        uid = self._get_uid()
        if not uid:
            return "LỖI: KHÔNG TÌM THẤY UID"

        for uid_ in uids:
            message = message + "\n" + f"@[{uid_[0]}:0]"

        message = message + "\n" + f"#{random_numbers()}"

        self.driver.get(f'https://mbasic.facebook.com/{uid}')
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
            except:
                print("Không có link để tắt preview.")
                return "ĐĂNG TRẠNG THÁI THÀNH CÔNG"
            
            return "ĐĂNG TRẠNG THÁI THÀNH CÔNG"
        except Exception as e:
            print(e)
            return "LỖI ĐĂNG TRẠNG THÁI KHÔNG THÀNH CÔNG"

    def quit(self) -> str:
        self.driver.quit()
        return "ĐÃ DỪNG LẠI"


def random_numbers() -> str:
    return ''.join(random.choices('0123456789', k=6))

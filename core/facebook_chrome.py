import os
import random
import signal
import time
import zipfile
from email.mime import image
from typing import Dict, List, Optional

import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ZIP_FILE_NAME = 'extension.zip'


class FacebookChrome:
    def __init__(self, cookies: str, proxy: Optional[str] = None):
        self.cookies = cookies
        self.proxy = proxy
        self.driver = None
        self.base_url = 'https://mbasic.facebook.com'
        self._setup_driver()

    def _setup_driver(self):
        self._create_extension_and_zip()
        self._initialize_webdriver()

    def _create_background_js(self, cookies_str):
        cookies = cookies_str.split(';')
        cookie_entries = []
        for cookie in cookies:
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                cookie_entries.append(f"""
                    {{
                        name: '{name.strip()}',
                        value: '{value.strip()}',
                        domain: '.facebook.com',
                        path: '/'
                    }}
                """)

        cookie_entries_str = ',\n    '.join(cookie_entries)

        background_js = """
        const cookies = [
            {cookie_entries}
        ];

        async function setCookies() {{
            for (const cookie of cookies) {{
                await chrome.cookies.set({{
                    url: `https://facebook.com`,
                    name: cookie.name,
                    value: cookie.value,
                    domain: cookie.domain.replace('.', ''),
                    path: cookie.path,
                }});
            }}
        }}

        function setCookiesUsingDocument(tabId) {{
            const cookieString = cookies
                .map((cookie) => `${{cookie.name}}=${{cookie.value}}`)
                .join('; ');
            chrome.scripting.executeScript({{
                target: {{ tabId: tabId }},
                func: (cookieString) => {{
                    document.cookie = cookieString;
                }},
                args: [cookieString],
            }});
        }}

        chrome.webNavigation.onCompleted.addListener(
            async (details) => {{
                await setCookies();

                chrome.tabs.query(
                    {{ active: true, currentWindow: true }},
                    function (tabs) {{
                        setCookiesUsingDocument(tabs[0].id);
                    }},
                );
            }},
            {{ url: [{{ hostContains: 'facebook.com' }}] }},
        );
        """.format(cookie_entries=cookie_entries_str)
        return background_js

    def _create_extension_and_zip(self):
        def create_extension_files(cookies_str):
            background_js = self._create_background_js(cookies_str)
            manifest_json = """
            {
                "background": {
                    "service_worker": "background.js"
                },
                "host_permissions": ["*://*.facebook.com/*"],
                "manifest_version": 3,
                "name": "Facebook",
                "permissions": ["cookies", "webNavigation", "activeTab", "scripting"],
                "version": "1.0"
            }
            """
            if os.path.exists('extension'):
                for file in os.listdir('extension'):
                    os.remove(os.path.join('extension', file))
            else:
                os.makedirs('extension')

            with open('extension/background.js', 'w') as f:
                f.write(background_js)
            with open('extension/manifest.json', 'w') as f:
                f.write(manifest_json)

        def zip_extension():
            if os.path.exists(ZIP_FILE_NAME):
                os.remove(ZIP_FILE_NAME)
            with zipfile.ZipFile(ZIP_FILE_NAME, 'w') as zipf:
                for root, dirs, files in os.walk('extension'):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(
                            os.path.join(root, file), 'extension'))

        create_extension_files(self.cookies)
        zip_extension()

    def _initialize_webdriver(self):
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument('--deny-permission-prompts')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-infobars')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "excludeSwitches", ['enable-automation'])
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile': {'password_manager_enabled': False}
        })
        options.add_experimental_option(
            'excludeSwitches', ['disable-popup-blocking'])

        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")
        extension_path = os.path.abspath(ZIP_FILE_NAME)
        options.add_extension(extension_path)

        self.driver = webdriver.Chrome(options=options)
        self.driver.get('https://mbasic.facebook.com')

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
            self.driver.get(self.base_url)
            time.sleep(2)
            self.driver.refresh()
            feed_compose = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.ID, 'mbasic_inline_feed_composer'))
            )
            if feed_compose:
                return "ĐĂNG NHẬP THÀNH CÔNG"
            else:
                return LOGIN_ERROR_MESSAGE
        except Exception as e:
            print(e)
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
            try:
                image_input = self.driver.find_element(By.NAME, 'file1')
            except:
                image_input = self.driver.find_element(By.NAME, 'pic')

            image_input.send_keys(image_path)
            try:
                post_button = self.driver.find_element(
                    By.XPATH, '//*[@id="root"]/table/tbody/tr/td/div/form/div[2]/input')
            except:
                post_button = self.driver.find_element(
                    By.CSS_SELECTOR, 'input[type="submit"][value="Save"]')
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
            message = message + "\n" + f"@[{uid_}:0]"

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
                        edit_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH,
                                 '//div[@aria-label="Actions for this post"]')
                            )
                        )
                        edit_button.click()
                        edit_post_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, '//span[text()="Edit post"]/parent::div/parent::div'))
                        )
                        edit_post_button.click()
                        remove_link_preview_button = WebDriverWait(self.driver, 10).until(
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
        except Exception as e:
            print(f"Lỗi khi đăng trạng thái: {e}")
            return "LỖI: ĐĂNG TRẠNG THÁI THẤT BẠI"

        return "ĐĂNG TRẠNG THÁI THÀNH CÔNG"

    def quit(self) -> str:
        self.driver.quit()
        return "ĐÃ DỪNG LẠI"

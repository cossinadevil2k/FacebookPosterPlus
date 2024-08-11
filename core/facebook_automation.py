import requests
from bs4 import BeautifulSoup
import json


class Facebook:
    def __init__(self, username=None, password=None, key_2fa=None, cookies=None):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://mbasic.facebook.com"
        self.headers = {
            "host": "mbasic.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9,id;q=0.8",
            "cache-control": "max-age=0",
            "upgrade-insecure-requests": "1",
        }
        self.session.headers.update(self.headers)
        self.cookies = cookies
        self.key_2fa = key_2fa

    def _get_login_form(self):
        fbml = self.session.get(f"{self.base_url}/fbml/ajax/dialog/")
        soup = BeautifulSoup(fbml.text, "html.parser")
        links = soup.find_all("a", {"class": True, "id": True})
        return links[1].get("href") if len(links) >= 2 else None

    def _submit_login_form(self, login_url):
        self.session.headers.update({"referer": f"{self.base_url}/fbml/ajax/dialog/"})
        ref = BeautifulSoup(self.session.options(login_url).text, "html.parser")
        form = ref.find("form", {"method": "post", "id": "login_form"})
        data = {x.get("name"): x.get("value") for x in form.find_all("input", {"type": "hidden", "value": True})}
        data.update({"email": self.username, "pass": self.password, "login": "Enter"})
        next_to = form.get("action")
        response = self.session.post(f"{self.base_url}{next_to}", data=data, headers={
            "content-length": "164",
            "content-type": "application/x-www-form-urlencoded",
            "origin": self.base_url,
            "referer": f"{self.base_url}{next_to}"
        })
        return response

    def _get_2f_code(self):
        if not self.key_2fa:
            return "error"
        url = f"https://2fa.live/tok/{self.key_2fa}"
        response = requests.get(url)
        data = response.json()
        token = data.get("token")
        return token

    def _submit_2fa_and_save_browser(self, response):
        ref = BeautifulSoup(response.text, "html.parser")
        form = ref.find("form", {"method": "post", "enctype": True})
        data = {x.get("name"): x.get("value") for x in form.find_all("input", {"type": "hidden", "value": True})}
        data.update({"submit[Submit Code]": "Submit Code"})
        code_2fa = self._get_2f_code()
        data.update({
            "approvals_code": code_2fa
        })
        response = self.session.post(f"{self.base_url}/login/checkpoint", data=data)
        ref = BeautifulSoup(response.text, "html.parser")

        # Save the browser.
        form = ref.find("form", {"method": "post", "action": "/login/checkpoint/"})
        # We are in save the browser page.
        if form:
            data = {x.get("name"): x.get("value") for x in form.find_all("input", {"type": "hidden", "value": True})}
            data.update({"submit[Continue]": "Continue"})
            self.session.post(f"{self.base_url}/login/checkpoint", data=data)
        self._format_cookies()

    def _format_cookies(self):
        cookies_dict = self.session.cookies.get_dict()
        result = [{'name': name, 'value': value} for name, value in cookies_dict.items()]
        return json.dumps(result)

    def login(self):
        login_url = self._get_login_form()
        if login_url:
            response = self._submit_login_form(login_url)
            try:
                if "checkpoint" in response.cookies:
                    self._submit_2fa_and_save_browser(response=response)
                elif "m_page_voice" in response.cookies:
                    return self._format_cookies()
                else:
                    return "Error"
            except Exception:
                return "Error"

        return "Error"

    def get_profile_uid(self):
        cookies = self.session.cookies.get_dict()
        uid = cookies.get('c_user') or cookies.get('m_page_voice')
        if not uid:
            raise ValueError("Không thể lấy UID từ cookie.")
        return uid

    def post_feed(self, content=None, uids=None):
        print("Đang chuẩn bị gửi bài viết...") # TODO: "Trả trạng thái về GUI"
        target_wall_url = f"{self.base_url}/{self.get_profile_uid()}"
        ref = BeautifulSoup(self.session.get(target_wall_url).text, "html.parser")
        form = ref.find("form", {"id": "mbasic-composer-form"})
        data = {x.get("name"): x.get("value") for x in form.find_all("input", {"type": "hidden", "value": True})}

        if uids:
            tags = []
            for uid in uids:
                tag = f"@[{uid[0]}:0]"
                tags.append(tag)
                print(f"Đang xử lý UID: {uid[0]}") # TODO: "Trả trạng thái về GUI"
            tags_str = "".join(tags)
            content = f"{content} {tags_str}"

        data.update({
            "view_post": "Đăng",
            "xc_message": content,
        })

        url = "https://mbasic.facebook.com/composer/mbasic/"
        response = self.session.post(url, data=data)
        if response.ok:
            print("Bài viết đã được đăng thành công.") # TODO: "Trả trạng thái về GUI"
        else:
            print("Có lỗi xảy ra khi gửi bài viết.") # TODO: "Trả trạng thái về GUI"

fb = Facebook("test", "test", "test")
fb.login()
# Phần trống trong danh sách UID sẽ được trả về giao diện GUI để cập nhật trạng thái.
# table(["UID", "Trạng thái"])
fb.post_feed(content="testttt", uids=[['100000984031847', '']])
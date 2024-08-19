import os
import sys
import time
from tkinter import Tk, filedialog

from core import FacebookChrome

TEXT_FILES_EXTENSION = "*.txt"
TEXT_FILES_DESCRIPTION = "Text files"


def read_lines_from_file(file_path: str) -> list[str]:
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]


def read_uids_from_file(file_path: str) -> list[str]:
    return read_lines_from_file(file_path)


def read_content(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file


def split_list(lst: list, chunk_size: int) -> list[list]:
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path)


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def select_file(prompt: str, filetypes: list) -> str:
    root = Tk()
    root.withdraw()
    icon_path = resource_path('icon.ico')
    if os.path.isfile(icon_path):
        root.iconbitmap(icon_path)

    file_path = filedialog.askopenfilename(title=prompt, filetypes=filetypes)
    return file_path


def main():
    cookies_file = select_file("Chọn tệp cookies", [(
        TEXT_FILES_DESCRIPTION, TEXT_FILES_EXTENSION)])
    if not cookies_file:
        print("Không chọn tệp cookies, thoát chương trình.")
        return

    uids_file = select_file(
        "Chọn tệp UIDs", [(TEXT_FILES_DESCRIPTION, TEXT_FILES_EXTENSION)])
    if not uids_file:
        print("Không chọn tệp UIDs, thoát chương trình.")
        return

    content_file = select_file("Chọn tệp nội dung", [(
        TEXT_FILES_DESCRIPTION, TEXT_FILES_EXTENSION)])
    if not content_file:
        print("Không chọn tệp nội dung, thoát chương trình.")
        return

    image_path = select_file(
        "Chọn tệp ảnh đại diện", [
            ("Image files", "*.jpg;*.jpeg;*.png")]
    )
    if not image_path:
        image_path = 'avatar.jpg'

    chunk_size_input = input(
        "Nhập kích thước phân chia UID (mặc định là 50): ")
    chunk_size = int(chunk_size_input) if chunk_size_input else 50
    proxy = input('Nhập Proxy(Dạng IP:PORT)')
    cookies_list = read_lines_from_file(cookies_file)
    uids = read_uids_from_file(uids_file)
    message = read_content(content_file)
    uid_chunks = split_list(uids, chunk_size)

    for i, cookies in enumerate(cookies_list):
        if i >= len(uid_chunks):
            break

        print(f"Processing account {i + 1} with cookies: {cookies}")
        fb_chrome = FacebookChrome(cookies, proxy)
        login_result = fb_chrome.login()
        print(login_result)

        if login_result == "ĐĂNG NHẬP THÀNH CÔNG":
            if file_exists(image_path):
                avatar_result = fb_chrome.change_avatar(image_path)
                print(avatar_result)
            else:
                print("Ảnh đại diện không tồn tại. Bỏ qua việc thay đổi ảnh đại diện.")

            uid_chunk = uid_chunks[i]
            post_result = fb_chrome.post_status(message, uid_chunk)
            print(post_result)

        quit_result = fb_chrome.quit()
        print(quit_result)
        time.sleep(5)


if __name__ == "__main__":
    main()

import base64

from PyQt5.QtCore import QBuffer, QFile, QIODevice, Qt, QTextStream, pyqtSignal
from PyQt5.QtGui import QIcon, QImage, QPixmap

from .components import (AccountInput, ButtonPanel, Footer, Header,
                         PostContent, ProxyInput, UIDInput)
from .resources import base64_icon, qss

from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                             QMessageBox, QVBoxLayout, QWidget, QMainWindow)

from PyQt5.QtCore import QBuffer, QIODevice, Qt, QThread, pyqtSignal
from core.facebook_chrome import FacebookChrome
import json
import time
import re

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._initUI()

    def _initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        icon_pixmap = self.base64_to_pixmap(base64_icon)
        icon = QIcon(icon_pixmap)
        self.setWindowIcon(icon)
        stylesheet = self._load_stylesheet("gui/style.qss")
        self.setStyleSheet(stylesheet)
        header = Header()
        footer = Footer()

        hero_section_layout = QHBoxLayout()

        left_section_layout = QVBoxLayout()
        self.account_input = AccountInput()
        self.uid_input = UIDInput()
        left_section_layout.addWidget(self.account_input, 3)
        left_section_layout.addWidget(self.uid_input, 2)

        right_section_layout = QVBoxLayout()
        self.proxy_input = ProxyInput()
        self.post_content = PostContent()
        self.button_panel = ButtonPanel()

        right_section_layout.addWidget(self.proxy_input)
        right_section_layout.addWidget(self.post_content)
        right_section_layout.addWidget(self.button_panel)

        hero_section_layout.addLayout(left_section_layout, 3)
        hero_section_layout.addLayout(right_section_layout, 1)
        hero_section_layout.addStretch()

        main_layout.addWidget(header)
        main_layout.addLayout(hero_section_layout)
        main_layout.addStretch()
        main_layout.addWidget(footer)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._set_window_size()
        self.button_panel.get_run_button().clicked.connect(self._run_task)
        self.button_panel.get_upload_button().clicked.connect(self._upload_photo)

        self.avatar = None

    def _set_window_size(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = screen_geometry.width() * 3 / 4
        height = screen_geometry.height() * 3 / 4
        self.resize(int(width), int(height))
        self.setFixedSize(int(width), int(height))
        self.setMinimumSize(int(width), int(height))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    def base64_to_pixmap(self, base64_str):
        image_data = base64.b64decode(base64_str)
        buffer = QBuffer()
        buffer.setData(image_data)
        buffer.open(QIODevice.ReadOnly)  # type: ignore
        image = QImage()
        image.loadFromData(buffer.data())
        pixmap = QPixmap.fromImage(image)
        return pixmap

    def _run_task(self):
        proxy = self.proxy_input.get_text()
        uids = self.uid_input.get_table_data()
        accounts = self.account_input.get_table_data()
        print(
            f"Running task with proxy: {proxy}, UIDs: {uids}, Accounts: {accounts}")
        
        for account in accounts:
            username, password, key_2fa, cookie, _ = account
            self.thread: Worker = Worker(username, password, key_2fa, proxy, self.post_content.get_content(), self.avatar)
            self.thread.result_signal.connect(self.handle_result)
            self.thread.start()

    def handle_result(self, result):
        try:
            result_dict = json.loads(result)
            status = result_dict.get("status")
            message = result_dict.get("message")

            if status == "ERROR":
                QMessageBox.critical(self, "Lỗi", message)
            else:
                QMessageBox.information(
                    self, "Thành công", "Hoạt động đã hoàn tất thành công")
        except json.JSONDecodeError:
            QMessageBox.critical(
                self, "Lỗi", "Dữ liệu trả về không hợp lệ")
        

    def _upload_photo(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.bmp)")
        file_dialog.setViewMode(QFileDialog.List)
        file_dialog.setOptions(options)

        if file_dialog.exec_():
            self.avatar = file_dialog.selectedFiles()
            QMessageBox.about(
                self, "Thông báo", f"Đã chọn hình ảnh avatar.")
            
        print(self.avatar)

    def _load_stylesheet(self, filename):
        file = QFile(filename)
        if not file.open(QFile.ReadOnly | QFile.Text):
            print(qss)
            return qss
        text_stream = QTextStream(file)
        return text_stream.readAll()


class Worker(QThread):
    result_signal = pyqtSignal(str)

    def __init__(self, username, password, key_2fa, proxy, content, avatar_path):
        super().__init__()
        self.username = username
        self.password = password
        self.key_2fa = key_2fa
        self.proxy = proxy
        self.content = content
        self.avatar_path = avatar_path

    def run(self):
        if self.username == '' or self.password == '' or self.key_2fa == '':
            self.result_signal.emit(
                '{"status": "ERROR", "message": "Chưa điền đủ thông tin đăng nhập"}')
            return
        elif self.content == '':
            self.result_signal.emit(
                '{"status": "ERROR", "message": "Chưa nhập nội dung bài viết"}')
            return
        if self.proxy != '' and not validate_proxy(self.proxy):
            self.result_signal.emit(
                '{"status": "ERROR", "message": "Proxy không hợp lệ"}')
            return
        try:
            chrome = FacebookChrome(
                self.username,
                self.password,
                self.key_2fa,
                self.proxy
            )
        except Exception as e:
            self.result_signal.emit(
                '{"status": "ERROR", "message": "' + str(e) + '"}')
            return
        status = chrome.login()
        if status != 'SUCCESS':
            self.result_signal.emit(
                '{"status": "ERROR", "message": "Thông tin tài khoản không hợp lệ"}')
            return
        try:
            if self.avatar_path:
                chrome.change_avatar(self.avatar_path)
            
            time.sleep(1)

            chrome.post_status(self.content)
        except FileNotFoundError:
            self.result_signal.emit(
                '{"status": "ERROR", "message": "Vui lòng lấy danh sách group trước!"}')
        except Exception as e:
            self.result_signal.emit(
                '{"status": "ERROR", "message": "' + str(e) + '"}')
            

def validate_proxy(proxy):
    pattern = r'^[^:]+:\d+$'
    return re.match(pattern, proxy) is not None
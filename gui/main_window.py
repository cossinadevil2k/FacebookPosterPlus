import base64
import threading

from PyQt5.QtCore import QBuffer, QIODevice, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                             QMessageBox, QTableWidgetItem, QVBoxLayout,
                             QWidget)

from core import FacebookChrome

from .components import (AccountInput, ButtonPanel, Footer, Header,
                         PostContent, ProxyInput, UIDInput)
from .resources import base64_icon, qss


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
        self.setStyleSheet(qss)
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
        user_ids = self.uid_input.get_table_data()
        account_list = self.account_input.get_table_data()
        avatar_file_path = self.button_panel.get_image_path()
        post_content = self.post_content.get_content()

        if not post_content:
            self.button_panel.toggle_run_state()
            QMessageBox.critical(self, "Lỗi", "Chưa điền nội dung bài đăng!")
            return

        if not user_ids:
            self.button_panel.toggle_run_state()
            QMessageBox.critical(self, "Lỗi", "Chưa cung cấp UID!")
            return

        def process_facebook_account(index, account_details):
            facebook_instance = FacebookChrome(
                username=account_details[0], password=account_details[1], proxy=proxy)
            login_status = facebook_instance.login()
            self.account_input.set_status(
                index, f"{login_status}")
            if "LỖI" in login_status:
                self.account_input.set_status_color(index, "red")
            self.account_input.table.setItem(index, 3, QTableWidgetItem(
                facebook_instance.get_cookie().get('c_user', 'COOKIE NOT FOUND')))
            if login_status == "ĐĂNG NHẬP THÀNH CÔNG" and avatar_file_path:
                avatar_status = facebook_instance.change_avatar(
                    avatar_file_path)
                status_message = f"{avatar_status}"
                self.account_input.set_status(index, status_message)
                if "LỖI" in avatar_status:
                    self.account_input.set_status_color(index, "red")
                QApplication.processEvents()

            if login_status == "ĐĂNG NHẬP THÀNH CÔNG":
                post_status = facebook_instance.post_status(
                    post_content, user_ids)
                self.uid_input.set_status('THÀNH CÔNG')
                status_message = f"{post_status}"
                self.account_input.set_status(index, status_message)
                if "LỖI" in post_status:
                    self.account_input.set_status_color(index, "red")
                else:
                    self.account_input.set_status_color(index, "green")
                QApplication.processEvents()

        threads = []
        for index, account in enumerate(account_list):
            thread = threading.Thread(
                target=process_facebook_account, args=(index, account))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        QMessageBox.information(
            self, "Hoàn thành", "Tất cả các tác vụ đã hoàn thành.")

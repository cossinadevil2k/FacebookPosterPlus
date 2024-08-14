import base64

from PyQt5.QtCore import QBuffer, QIODevice, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                             QMessageBox, QTableWidgetItem, QVBoxLayout,
                             QWidget)

from core import FacebookChrome

from .components import (AccountInput, ButtonPanel, Footer, Header,
                         PostContent, ProxyInput, UIDInput)
from .resources import base64_icon, qss
import json

BATCH_UID = 2

class WorkerThread(QThread):
    update_status = pyqtSignal(int, str, str)
    update_uid_status = pyqtSignal(str)
    update_cookies = pyqtSignal(int, str)
    finished = pyqtSignal(str)  # Ensure this signal has one argument

    def __init__(self, index, account_details, proxy, post_content, user_ids, avatar_file_path):
        super().__init__()
        self.index = index
        self.account_details = account_details
        self.proxy = proxy
        self.post_content = post_content
        self.user_ids = user_ids
        self.avatar_file_path = avatar_file_path
        self.facebook_instance = None
        self._stop_requested = False

    def run(self):
        self.facebook_instance = FacebookChrome(
            username=self.account_details[0], password=self.account_details[1], key_2fa=self.account_details[2], proxy=self.proxy)
        login_status = self.facebook_instance.login()
        if self._stop_requested:
            self.finished.emit("ĐÃ DỪNG LẠI")
            return
        self.update_status.emit(self.index, login_status,
                                'red' if "LỖI" in login_status else '')
        if "LỖI" in login_status:
            self.finished.emit("ĐĂNG NHẬP THẤT BẠI")
            return

        cookies = self.facebook_instance.get_cookies()
        cookies_str = json.dumps(cookies)
        self.update_cookies.emit(self.index, cookies_str)

        if login_status == "ĐĂNG NHẬP THÀNH CÔNG" and self.avatar_file_path:
            avatar_status = self.facebook_instance.change_avatar(
                self.avatar_file_path)
            self.update_status.emit(
                self.index, avatar_status, 'red' if "LỖI" in avatar_status else '')

        if login_status == "ĐĂNG NHẬP THÀNH CÔNG":
            post_status = self.facebook_instance.post_status(
                self.post_content, self.user_ids)
            self.update_uid_status.emit('THÀNH CÔNG')
            self.update_status.emit(
                self.index, post_status, 'red' if "LỖI" in post_status else 'green')

        self.finished.emit("HOÀN TẤT")

    def stop(self):
        self._stop_requested = True
        if self.facebook_instance:
            status = self.facebook_instance.quit()
            self.finished.emit(status)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._initUI()
        self.workers = []
        self.worker_count = 0
        self.completed_workers = 0

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
        self.button_panel = ButtonPanel(self)

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
        self.button_panel.toggle_run_state(True)
        if not post_content:
            self.button_panel.toggle_run_state(False)
            QMessageBox.critical(self, "Lỗi", "Chưa điền nội dung bài đăng!")
            return
        if not user_ids:
            self.button_panel.toggle_run_state(False)
            QMessageBox.critical(self, "Lỗi", "Chưa cung cấp UID!")
            return

        def update_status(index, status, color):
            self.account_input.set_status(index, status)
            self.account_input.set_status_color(index, color)
            QApplication.processEvents()

        def update_uid_status(status):
            self.uid_input.set_status(status)
            QApplication.processEvents()

        def update_cookies(index, cookies):
            if 0 <= index < self.account_input.table.rowCount():
                cookie_item = QTableWidgetItem(cookies)
                self.account_input.table.setItem(index, 3, cookie_item)
            QApplication.processEvents()

        def worker_finished(status):
            self.completed_workers += 1
            if self.completed_workers == self.worker_count:
                self.button_panel.toggle_run_state(False)
                QMessageBox.information(
                    self, "Hoàn tất", f"Chạy hoàn tất! Trạng thái: {status}")

        self.workers = []
        self.worker_count = len(account_list)
        self.completed_workers = 0

        for index, account in enumerate(account_list):
            uids = user_ids[(index*BATCH_UID) : (index*BATCH_UID) + BATCH_UID]

            if not uids:
                uids = user_ids[:BATCH_UID]

            worker = WorkerThread(index, account, proxy,
                                  post_content, uids, avatar_file_path)
            worker.update_status.connect(update_status)
            worker.update_uid_status.connect(update_uid_status)
            worker.update_cookies.connect(update_cookies)
            worker.finished.connect(worker_finished)
            self.workers.append(worker)
            worker.start()

    def stop_all_workers(self):
        for worker in self.workers:
            worker.stop()
            worker.wait()
        self.button_panel.toggle_run_state(False)

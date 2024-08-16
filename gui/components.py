import os
import webbrowser

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QCursor, QKeyEvent
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from .resources import APP_NAME, qss_start, qss_stop


class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title_label = QLabel(f"{APP_NAME}")
        title_label.setCursor(QCursor(Qt.PointingHandCursor))
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.mousePressEvent = self.open_copyright

        layout.addWidget(title_label)
        layout.addStretch()
        self.setLayout(layout)

    def open_copyright(self, event):
        webbrowser.open("https://t.me/tripleseven190504")


class ProxyInput(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Proxy (Dạng IP:PORT)")
        self.input = QLineEdit()
        self.input.setPlaceholderText("VD: 192.168.1.1:8080")
        self.input.setObjectName('proxy_input')
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)
        self.setLayout(self.layout)

    def get_text(self):
        return self.input.text()


class UIDInput(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Danh sách UID cần gắn thẻ:")

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["UID", "Trạng thái"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setToolTip("Nhấn chuột phải để dán danh sách UID")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.handle_paste)

    def delete_selected_row(self):
        selected_ranges = self.table.selectedRanges()
        if selected_ranges:
            for selection in selected_ranges:
                top_row = selection.topRow()
                bottom_row = selection.bottomRow()
                for row in range(bottom_row, top_row - 1, -1):
                    self.table.removeRow(row)

    def handle_paste(self):
        clipboard = QApplication.clipboard()
        data = clipboard.text().strip().split('\n')
        for line in data:
            self.add_uid(line)

    def add_uid(self, uid):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(uid))
        self.table.setItem(row_position, 1, QTableWidgetItem(""))

    def get_table_data(self):
        data = []
        for row in range(self.table.rowCount()):
            uid_item = self.table.item(row, 0)
            status_item = self.table.item(row, 1)
            data.append([uid_item.text() if uid_item is not None else "",
                         status_item.text() if status_item is not None else ""])
        return data

    def set_status(self, status_texts):
        def update_row(row):
            if row < len(status_texts):
                status_item = self.table.item(row, 1)
                if status_item:
                    status_item.setText(status_texts[row])
                QTimer.singleShot(500, lambda: update_row(row + 1))
        update_row(0)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_row()
        super().keyPressEvent(event)

    def show_error_message(self, message):
        QMessageBox.warning(self, "Lỗi", message)


class AccountInput(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Danh sách tài khoản:")

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Tài khoản", "Mật khẩu", "Mã 2FA", "Cookie", "Trạng thái"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setToolTip(
            "Nhấn chuột phải để dán danh sách tài khoản clone!")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.handle_paste)

    def delete_selected_row(self):
        selected_ranges = self.table.selectedRanges()
        if selected_ranges:
            for selection in selected_ranges:
                top_row = selection.topRow()
                bottom_row = selection.bottomRow()
                for row in range(bottom_row, top_row - 1, -1):
                    self.table.removeRow(row)

    def handle_paste(self):
        clipboard = QApplication.clipboard()
        data = clipboard.text().strip().split('\n')
        for line in data:
            account_info = line.split('|')
            if 3 <= len(account_info) <= 4:
                account_info.extend([''] * (5 - len(account_info)))
                self.add_account(account_info)
            else:
                self.show_error_message(
                    f"Dữ liệu đầu vào không hợp lệ: {line}")
                break

    def add_account(self, account_info):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        for i, info in enumerate(account_info):
            self.table.setItem(row_position, i, QTableWidgetItem(info))

    def get_table_data(self):
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                row_data.append(item.text() if item is not None else "")
            data.append(row_data)
        return data

    def set_status(self, row, status_text):
        if 0 <= row < self.table.rowCount():
            status_item = self.table.item(row, 4)
            if status_item:
                status_item.setText(status_text)

    def set_status_color(self, row, color):
        if 0 <= row < self.table.rowCount():
            status_item = self.table.item(row, 4)
            if status_item:
                status_item.setBackground(QColor(color))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_selected_row()
        super().keyPressEvent(event)

    def show_error_message(self, message):
        QMessageBox.warning(self, "Lỗi", message)


class PostContent(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Nội dung bài viết:")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Nhập nội dung bài viết tại đây")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_edit)
        self.setLayout(self.layout)

    def get_content(self):
        return self.text_edit.toPlainText()


class ButtonPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.button_layout = QVBoxLayout()

        self.upload_button = QPushButton("Chọn ảnh đại diện")
        self.upload_button.setToolTip("Chọn ảnh đại diện cho account!")
        self.upload_button.setCursor(QCursor(Qt.OpenHandCursor))
        self.upload_button.clicked.connect(self._select_image)

        self.run_button = QPushButton("Bắt đầu chạy")
        self.run_button.setToolTip("Nhấn để bắt đầu chạy")
        self.run_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.image_path = None
        self.running = False

        self.button_layout.addWidget(self.upload_button)
        self.button_layout.addWidget(self.run_button)

        self.setLayout(self.button_layout)
        self._update_button_style()

    def _select_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setOptions(QFileDialog.ReadOnly)
        file_dialog.setWindowTitle("Chọn ảnh đại diện")
        file_dialog.setNameFilter(
            "Ảnh (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)")
        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                file_name = os.path.basename(file_path)
                self.upload_button.setText(f"Đã chọn: {file_name}")
                self.image_path = file_path

    def toggle_run_state(self, is_running=None):
        if is_running is not None:
            self.running = is_running

        if self.running:
            self.run_button.setText("Dừng lại")
            self.run_button.setToolTip("Nhấn để dừng lại")
            self.run_button.clicked.disconnect()
            self.run_button.clicked.connect(
                self.parent_window.stop_all_workers)
        else:
            self.run_button.setText("Bắt đầu chạy")
            self.run_button.setToolTip("Nhấn để bắt đầu chạy")
            self.run_button.clicked.disconnect()
            self.run_button.clicked.connect(
                self.parent_window._run_task)
        self._update_button_style()

    def _update_button_style(self):
        if self.running:
            self.run_button.setStyleSheet(qss_stop)
        else:
            self.run_button.setStyleSheet(qss_start)

    def get_run_button(self):
        return self.run_button

    def get_image_path(self):
        return self.image_path


class Footer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        copyright_label = QLabel("Copyright © 2024 OvFTeam")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setCursor(QCursor(Qt.PointingHandCursor))
        copyright_label.mousePressEvent = self.open_copyright
        layout.addWidget(copyright_label)
        layout.addStretch()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)

    def open_copyright(self, event):
        webbrowser.open("https://t.me/Trungtdd")

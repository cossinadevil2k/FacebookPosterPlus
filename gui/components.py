import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QKeyEvent
from PyQt5.QtWidgets import (QApplication, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

APP_NAME = "FacebookPosterPlus"


class Header(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title_label = QLabel(f"{APP_NAME}")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addStretch()
        self.setLayout(layout)


class ProxyInput(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Proxy (Dạng IP:PORT)")
        self.input = QLineEdit()
        self.input.setPlaceholderText("VD: 192.168.1.1:8080")
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
            if len(account_info) == 3:
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
    def __init__(self):
        super().__init__()
        self.button_layout = QVBoxLayout()

        self.upload_button = QPushButton("Chọn ảnh đính kèm")
        self.upload_button.setToolTip("Chọn tệp ảnh để đính kèm vào bài viết")
        self.run_button = QPushButton("Bắt đầu chạy")
        self.run_button.setToolTip("Nhấn để bắt đầu thực hiện các hành động")

        self.button_layout.addWidget(self.upload_button)
        self.button_layout.addWidget(self.run_button)

        self.setLayout(self.button_layout)

    def get_upload_button(self):
        return self.upload_button

    def get_run_button(self):
        return self.run_button


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
        copyright_label.setToolTip("Nhấp để mở trang web của OvFTeam")
        copyright_label.mousePressEvent = self.open_copyright
        layout.addWidget(copyright_label)
        layout.addStretch()
        self.setLayout(layout)
        self.setContentsMargins(0, 0, 0, 0)

    def open_copyright(self, event):
        webbrowser.open("https://t.me/Trungtdd")

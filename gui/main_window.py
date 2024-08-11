import base64

from PyQt5.QtCore import QBuffer, QFile, QIODevice, Qt, QTextStream
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                             QVBoxLayout, QWidget)

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

    def _upload_photo(self):
        print("SOS...")

    def _load_stylesheet(self, filename):
        file = QFile(filename)
        if not file.open(QFile.ReadOnly | QFile.Text):
            print(qss)
            return qss
        text_stream = QTextStream(file)
        return text_stream.readAll()

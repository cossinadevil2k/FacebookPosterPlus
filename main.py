import sys

from PyQt5.QtWidgets import QApplication

from gui import APP_NAME, MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle(APP_NAME)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QTabWidget, QDesktopWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess, QTimer, QUrl
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QDesktopServices


class CommandExecutor(QThread):
    command_output = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        process = QProcess()
        self.command_output.emit(f"impacket-GUI > {self.command}")
        process.readyReadStandardOutput.connect(self.handle_output)
        process.finished.connect(self.finished)

        process.start(self.command)
        process.waitForFinished(-1)

        output_data = process.readAllStandardOutput().data()
        output = self.decode_output(output_data)
        self.command_output.emit(output)

    def handle_output(self):
        output_data = self.sender().readAllStandardOutput().data()
        output = self.decode_output(output_data)
        self.command_output.emit(output)

    def decode_output(self, output_data):
        encodings = ['utf-8', 'gb2312']  # Try different encodings

        for encoding in encodings:
            try:
                output = output_data.decode(encoding).strip()
                return output
            except UnicodeDecodeError:
                pass

        # If all encodings fail, return an empty string
        return ''

class ImpacketExecutor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Impacket-GUI")
        self.resize(800, 1200)
        self.setWindowIcon(QIcon("./logo.jpg"))  # Replace with your logo image path
        self.setFont(QFont('Microsoft YaHei', 12))
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()

        tabs = ["PSEXEC", "WMIEXEC", "ATEXEC"]
        self.executor_threads = []

        for tab_name in tabs:
            tab = QWidget()
            self.init_tab(tab, tab_name)
            self.tab_widget.addTab(tab, tab_name)

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        # Add the "About" button
        about_button = QPushButton("About")
        about_button.clicked.connect(self.open_about_url)
        layout.addWidget(about_button)

        self.setLayout(layout)

    def init_tab(self, tab, tab_name):
        ip_label = QLabel("IP:")
        ip_entry = QLineEdit()
        username_label = QLabel("Username:")
        username_entry = QLineEdit()
        password_label = QLabel("Password:")
        password_entry = QLineEdit()
        password_entry.setEchoMode(QLineEdit.Password)
        hashes_label = QLabel("Hashes:")
        hashes_entry = QLineEdit()
        command_label = QLabel(f"Command for {tab_name}:")
        command_entry = QLineEdit()
        result_text = QTextEdit()
        result_text.setReadOnly(True)

        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(lambda: self.execute_command(tab_name, ip_entry.text(), username_entry.text(), password_entry.text(), hashes_entry.text(), command_entry.text(), result_text))

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(ip_label)
        tab_layout.addWidget(ip_entry)
        tab_layout.addWidget(username_label)
        tab_layout.addWidget(username_entry)
        tab_layout.addWidget(password_label)
        tab_layout.addWidget(password_entry)
        tab_layout.addWidget(hashes_label)
        tab_layout.addWidget(hashes_entry)
        tab_layout.addWidget(command_label)
        tab_layout.addWidget(command_entry)
        tab_layout.addWidget(execute_button)
        tab_layout.addWidget(result_text)

        tab.setLayout(tab_layout)


    def open_about_url(self):
        # Define your about URL here
        about_url = "https://github.com/yutianqaq/impacket-gui"
        QDesktopServices.openUrl(QUrl(about_url))

    def execute_command(self, tab_name, ip, username, password, hashes, command, result_text):
        cmd = f"python .\examples\{tab_name.lower()}.py {username}:{password}@{ip} {command} -codec utf-8"
        if hashes:
            cmd = f"python .\examples\{tab_name.lower()}.py {username}@{ip} {command} -hashes 00000000000000000000000000000000:{hashes} -codec utf-8"

        executor = CommandExecutor(cmd)
        executor.command_output.connect(result_text.append)
        executor.finished.connect(executor.deleteLater)

        executor_thread = QThread()
        executor.moveToThread(executor_thread)
        executor_thread.started.connect(executor.run)
        executor_thread.finished.connect(executor_thread.deleteLater)

        self.executor_threads.append(executor_thread)
        executor_thread.start()

        # Allow the GUI to update while the command is running
        while executor_thread.isRunning():
            QCoreApplication.processEvents()

    def closeEvent(self, event):
        # Ensure that all executor threads and their associated processes are terminated
        for executor_thread in self.executor_threads:
            executor_thread.quit()
            executor_thread.wait()

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    executor = ImpacketExecutor()
    executor.show()
    sys.exit(app.exec_())

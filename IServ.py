# -*- coding: utf-8 -*-
import json
import os
import random
import getpass
import socket
import stat
import sys
from time import sleep

from win10toast import ToastNotifier
import requests
import simplejson
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QUrl, QDir, QThreadPool, QRunnable, pyqtSignal, QObject, Qt, QPoint
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt5 import QtWebEngineWidgets

import resource_rc
import window
# noinspection PyUnresolvedReferences
from AccListHandler import AccListHandler


class Page(QtWebEngineWidgets.QWebEnginePage):
    def createWindow(self, _type):
        page = Page(self)
        page.urlChanged.connect(self.on_url_changed)
        return page

    def on_url_changed(self, url):
        page = self.sender()
        self.setUrl(url)
        page.deleteLater()

    def acceptNavigationRequest(self, url: QtCore.QUrl, type_: 'QtWebEngineWidgets.QWebEnginePage.NavigationType',
                                isMainFrame: bool) -> bool:
        if not url.host() == QUrl("https://" + w.acc['host']).host():
            if type_ == QtWebEngineWidgets.QWebEnginePage.NavigationTypeLinkClicked or type_ == QtWebEngineWidgets. \
                    QWebEnginePage.NavigationTypeTyped:
                QtGui.QDesktopServices.openUrl(url)
            w.ignore_not_successful = True
            return False
        elif type_ == QtWebEngineWidgets.QWebEnginePage.NavigationTypeLinkClicked and url.toDisplayString() \
                .__contains__("/iserv/mail?path=INBOX&msg="):
            w.ignore_not_successful = True
            return True
        else:
            return True


# noinspection PyUnresolvedReferences
class Window(QtWidgets.QWidget, window.Ui_Window):
    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)

        self.fullscreenButton.clicked.connect(self.toggle_full_screen)
        self.fullscreenButton_2.clicked.connect(self.toggle_full_screen)

        # Account
        self.acc = None
        self.uid = None

        # Threads
        self.threadpool = QThreadPool()
        self.tmpPath = QDir.tempPath() + "/IServCache/"

        # acc_page
        self.update_acc_view()
        self.acc_listview.clicked.connect(self.acc_clicked)
        self.add_button.clicked.connect(self.add_acc_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)

        # add_acc_page
        self.error_label.setStyleSheet("color: red")
        self.cancel_button.clicked.connect(self.cancel_button_clicked)
        self.accept_button.clicked.connect(self.ok_clicked)

        # web_view_page
        self.login_not_started = True
        self.ignore_not_successful = False

        self.download = None
        self.file = None

        self.webView.loadFinished.connect(self.load_finished)
        self.webView.urlChanged.connect(self.url_changed)

        self.webView.setPage(Page(self.webView))

        self.webView.page().profile().downloadRequested.connect(self.download_requested)

        self.back.clicked.connect(self.back_clicked)
        self.forward.clicked.connect(self.forward_clicked)
        self.reload.clicked.connect(self.reload_clicked)

        # last_widget
        self.last_widget = self.account_page

        # NotificationOpen
        self.notification_url = ""
        self.notification_url_loaded = False
        sig.openNotificationUrl.connect(self.open_notification_url)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        # Splash Loading Screen
        if not acc_list_handler.acc_list_exist():
            self.stackedWidget.setCurrentWidget(self.add_account_page)
            self.cancel_button.hide()
        else:
            self.stackedWidget.setCurrentWidget(self.account_page)
        movie = QMovie(":/pictures/Loader.gif")
        self.loading_label.setMovie(movie)
        self.loading_label.movie().start()

    # Key Press Event
    def keyPressEvent(self, key_event: QtGui.QKeyEvent) -> None:
        if key_event.key() == Qt.Key_Return and self.stackedWidget.currentWidget() == self.add_account_page:
            self.ok_clicked()
        if key_event.key() == Qt.Key_F11:
            self.toggle_full_screen()

    # acc_page
    def update_acc_view(self):
        for i in acc_list_handler.accList:
            self.acc_listview.addItem(i["email"])

    def acc_clicked(self, index):
        if self.delete_button.isChecked():
            acc_list_handler.delete_acc(index.row())
            self.acc_listview.clear()
            self.update_acc_view()
            if acc_list_handler.accList.__len__() == 0:
                self.stackedWidget.setCurrentWidget(self.add_account_page)
                self.cancel_button.hide()
        else:
            self.acc = acc_list_handler.get_login_data(index.row())
            self.stackedWidget.setCurrentWidget(self.loading_page)
            self.last_widget = self.account_page

            self.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
            self.info_label.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")

    def add_acc_clicked(self):
        self.stackedWidget.setCurrentWidget(self.add_account_page)

    def delete_button_clicked(self):
        if self.delete_button.isChecked():
            self.info_error_label.setStyleSheet("color: blue")
            self.info_error_label.setText("Klick auf einen Account um ihn zu löschen")
            self.info_error_label.show()
        else:
            self.info_error_label.hide()

    # add_acc_page
    def cancel_button_clicked(self):
        self.stackedWidget.setCurrentWidget(self.account_page)
        self.email_lineEdit.clear()
        self.password_lineEdit.clear()
        self.acc_listview.clearFocus()
        self.delete_button.setChecked(False)

    def ok_clicked(self):
        self.error_label.hide()
        if not str(self.email_lineEdit.text()).__contains__("@") \
                or not str(self.email_lineEdit.text()).__contains__("."):
            self.error_label.setText("Bitte geben Sie eine gültige IServ-Email-Adresse ein")
            self.error_label.show()
        elif not self.password_lineEdit.text():
            self.error_label.setText("Bitte geben Sie ein Passwort ein")
            self.error_label.show()
        if not self.error_label.isVisible():
            uid = acc_list_handler.add_acc(self.email_lineEdit.text(), self.password_lineEdit.text())
            if not uid == -1:
                self.acc = acc_list_handler.get_login_data(uid)
                self.uid = uid
                self.last_widget = self.add_account_page
                self.stackedWidget.setCurrentWidget(self.loading_page)
                self.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
                self.info_label.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")
            else:
                self.error_label.setText("Account wurde bereits hinzugefügt!")
                self.error_label.show()

    # web_view_page
    def load_finished(self, successful):
        if not successful:
            if not self.ignore_not_successful:
                if self.last_widget == self.account_page:
                    self.info_error_label.setText(
                        "Ein Fehler ist aufgetreten!")
                    self.info_error_label.setStyleSheet("color: red")
                    self.info_error_label.show()
                else:
                    self.error_label.setText("Ein Fehler ist aufgetreten!")
                    self.error_label.setStyleSheet("color: red")
                    self.error_label.show()
                    acc_list_handler.delete_acc(self.uid)
                self.stackedWidget.setCurrentWidget(self.last_widget)
            else:
                self.ignore_not_successful = False
        else:
            if self.webView.url().__eq__(
                    QUrl("https://" + self.acc["host"] + "/iserv/login")) & self.login_not_started:
                self.info_label.setText("Login für " + self.acc["email"] + " wird ausgeführt")
                self.login_not_started = False
                self.webView.page().runJavaScript(
                    "document.getElementsByName('_username').item(0).value='" + self.acc["username"] + "'")
                self.webView.page().runJavaScript(
                    "document.getElementsByName('_password').item(0).value='" + self.acc["password"] + "'")
                self.webView.page().runJavaScript("document.forms[0].submit()")
            elif self.webView.url().__eq__(QUrl("https://" + self.acc["host"] + "/iserv/login")):
                if self.last_widget == self.account_page:
                    self.info_error_label.setText("Login nicht erfolgreich!")
                    self.info_error_label.setStyleSheet("color: red")
                    self.info_error_label.show()
                    self.login_not_started = True
                else:
                    self.error_label.setText("Login nicht erfolgreich!")
                    self.info_error_label.setStyleSheet("color: red")
                    self.error_label.show()
                    acc_list_handler.delete_acc(self.uid)
                    self.login_not_started = True
                w.stackedWidget.setCurrentWidget(self.last_widget)
            elif self.webView.url() == QUrl("https://" + self.acc["host"] + "/iserv/"):
                if not self.notification_url == "":
                    if not self.notification_url_loaded:
                        self.webView.load(QUrl("https://" + self.acc["host"] + self.notification_url))
                        self.notification_url_loaded = True
                        self.notification_url = ""
                self.stackedWidget.setCurrentWidget(self.webview_page)
                self.set_disabled_state_web_controls(False)
            else:
                self.set_disabled_state_web_controls(False)

    def url_changed(self, url):
        self.url_label.setText(url.toString())
        if url == QUrl("https://" + self.acc["host"] + "/iserv/app/login") and not self.login_not_started:
            self.login_not_started = True
            self.notification_url_loaded = False
            self.cancel_button.show()
            self.email_lineEdit.clear()
            self.password_lineEdit.clear()
            self.delete_button.setChecked(False)
            self.acc_listview.clear()
            self.update_acc_view()
            self.acc_listview.clearFocus()
            self.error_label.clear()
            self.info_error_label.clear()
            self.stackedWidget.setCurrentWidget(self.account_page)

    def download_requested(self, download):
        self.stackedWidget.setCurrentWidget(self.webview_page)
        acc_list_handler.add_acc(self.acc["email"], self.acc["password"])
        self.info_error_label.clear()
        self.error_label.clear()
        path = str(download.path()).split("/")
        file = path[len(path) - 1]
        download.setPath(self.tmpPath + file)
        self.download = download
        self.file = file

        download.accept()
        download.finished.connect(self.download_finished)

    def download_finished(self):
        os.chmod(self.tmpPath + self.file, stat.S_IREAD)
        os.startfile(self.download.path())

    def back_clicked(self):
        self.set_disabled_state_web_controls(True)
        self.webView.back()

    def forward_clicked(self):
        self.set_disabled_state_web_controls(True)
        self.webView.forward()

    def reload_clicked(self):
        self.set_disabled_state_web_controls(True)
        self.webView.reload()

    def set_disabled_state_web_controls(self, state):
        self.back.setDisabled(state)
        self.forward.setDisabled(state)
        self.reload.setDisabled(state)

    def open_notification_url(self, user_data):
        self.show()
        self.stackedWidget.setCurrentWidget(self.loading_page)
        self.acc = user_data['acc']
        self.notification_url = user_data['url']
        self.notification_url_loaded = False
        self.last_widget = self.account_page
        self.webView.load(QUrl("http://" + self.acc['host'] + "/iserv/login"))
        self.info_label.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        point = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + point.x(), self.y() + point.y())
        self.oldPos = event.globalPos()

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.fullscreenButton.setIcon(QIcon(":/pictures/fullscreen.png"))
            self.showNormal()
        else:
            self.fullscreenButton.setIcon(QIcon(":/pictures/exit_fullscreen.png"))
            self.showFullScreen()

    def close_w(self):
        self.showNormal()
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
        self.hide()
        if self.stackedWidget.currentWidget() == self.webview_page:
            self.webView.load(QUrl("http://" + self.acc["host"] + "/iserv/app/logout"))
            self.stackedWidget.setCurrentWidget(self.loading_page)


class MySignals(QObject):
    showWindowRequested = pyqtSignal()
    openNotificationUrl = pyqtSignal(dict)


class SocketListener(QRunnable):
    def run(self) -> None:
        global socket_listener_running
        while socket_listener_running:
            try:
                s.listen(5)
                received_socket = s.accept()
                a = received_socket[0].recv(1024)
                if a == b'IServAppWindow':
                    sig.showWindowRequested.emit()
            except OSError:
                pass


class NotificationLookupService(QRunnable):
    def run(self) -> None:
        icon = "C:/Users/Philipp/AppData/Local/IServ/ICON.png"
        displayed_notifications = []
        global notify_service_running
        while notify_service_running:
            try:
                for acc in acc_list_handler.accList:
                    data = {
                        '_username': acc["username"],
                        '_password': acc["password"]
                    }
                    try:
                        response = requests.post('https://' + acc["host"] + '/iserv/app/login',
                                                 params=(('target', '/iserv/user/api/notifications'),),
                                                 data=data)
                    except requests.exceptions.ConnectionError:
                        continue
                    try:
                        notifications = response.json()['data']['notifications']
                    except KeyError:
                        continue
                    except simplejson.errors.JSONDecodeError:
                        continue
                    for notification in notifications:
                        if not displayed_notifications.__contains__(notification):
                            if self.all_signs_necessary(notification['title'], notification['content']):
                                tray_icon.showMessage(notification['message'], notification['title'] +
                                                      ": " + notification['content'] +
                                                      " ⋅ " + acc["email"], QIcon(":/pictures/ICON.png"))
                            elif self.all_signs_unnecessary(notification['title'], notification['content']):
                                tray_icon.showMessage(notification['message'], acc["email"],
                                                      QIcon(":/pictures/ICON.png"))
                            else:
                                if notification['title'] == "":
                                    tray_icon.showMessage(notification['message'], notification['content'] +
                                                          " ⋅ " + acc["email"], QIcon(":/pictures/ICON.png"))
                                if notification['content'] == "":
                                    tray_icon.showMessage(notification['message'], notification['title'] +
                                                          " ⋅ " + acc["email"], QIcon(":/pictures/ICON.png"))
                            displayed_notifications.append(notification)
            except RuntimeError:
                pass
            i = 0
            while i <= 120:
                i += 1
                sleep(1)
                if not notify_service_running:
                    break

    @staticmethod
    def all_signs_necessary(title, content):
        if not title == "" and not content == "":
            return True
        else:
            return False

    @staticmethod
    def all_signs_unnecessary(title, content):
        if title == "" and content == "":
            return True
        else:
            return False

    @staticmethod
    def open_notification(t):
        # noinspection PyUnresolvedReferences
        sig.openNotificationUrl.emit(t)


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(":/pictures/ICON.png"))
        self.setContextMenu(QMenu("IServ App"))
        self.contextMenu().addAction("Fenster öffnen/schließen", self.open_close)
        self.contextMenu().addAction("Beenden", self.exit)
        self.activated.connect(self.was_activated)

    @staticmethod
    def open_close():
        if w.isVisible():
            w.hide()
        else:
            w.show()

    @staticmethod
    def exit():
        app.exit(0)
        global notify_service_running
        notify_service_running = False
        sock = socket.socket()
        global address
        sock.connect(address)
        sock.send(b'0')
        global socket_listener_running
        socket_listener_running = False
        s.close()

    def was_activated(self, reason):
        if reason == QSystemTrayIcon.MiddleClick:
            self.exit()
        if reason == QSystemTrayIcon.Trigger:
            self.open_close()


def finalize_port_bind_server(bad_ports, port_=random.randint(2000, 65534)):
    if bad_ports.__contains__(port_):
        port_ = random.randint(2000, 65534)
        finalize_port_bind_server(bad_ports, port_)
    else:
        try:
            global s
            s.bind(('localhost', port_))
            return port_
        except socket.error:
            bad_ports.append(port_)
            s = socket.socket()
            finalize_port_bind_server(bad_ports)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    s = socket.socket()
    port_file_dir = str(QDir.tempPath()) + "/IServPort"
    try:
        port_file = open(port_file_dir, "r+")
    except FileNotFoundError:
        port_file = open(port_file_dir, "w+")
        os.chmod(port_file_dir, stat.S_IROTH + stat.S_IWOTH + stat.S_IRUSR + stat.S_IWUSR)

    port_file_str = port_file.read()

    if len(port_file_str) == 0:
        port = finalize_port_bind_server(bad_ports=[26000])
        address = ("localhost", port)
        port_file.write(json.dumps({getpass.getuser(): port}))
        port_file.close()
    else:
        port_dict: dict = json.loads(port_file_str)
        if port_dict.__contains__(str(getpass.getuser())):
            address = ("localhost", port_dict[str(getpass.getuser())])
            x = True
            try:
                s.connect(address)
            except ConnectionRefusedError:
                port_dict.__delitem__(str(getpass.getuser()))
                port = finalize_port_bind_server(bad_ports=[26000])
                address = ("localhost", port)
                port_dict[str(getpass.getuser())] = port
                port_file.seek(0)
                port_file.truncate(0)
                port_file.write(json.dumps(port_dict))
                port_file.close()
                x = False
            except TypeError:
                port_dict.__delitem__(str(getpass.getuser()))
                port = finalize_port_bind_server(bad_ports=[26000])
                address = ("localhost", port)
                port_dict[str(getpass.getuser())] = port
                port_file.seek(0)
                port_file.truncate(0)
                port_file.write(json.dumps(port_dict))
                port_file.close()
                x = False
            if x:
                if sys.argv.__contains__("--no-window"):
                    message_box = QMessageBox(QMessageBox.Warning, "IServ Tray Icon", "IServ Tray Icon is already "
                                              + "running")
                    message_box.exec_()
                    sys.exit(0)
                s.send(b'IServAppWindow')
                s.close()
                sys.exit(0)
        else:
            port_file.seek(0)
            port_file.truncate(0)
            port = finalize_port_bind_server(bad_ports=[26000])
            address = ("localhost", port)
            port_dict[str(getpass.getuser())] = port
            port_file.write(json.dumps(port_dict))
            port_file.close()

    threadpool = QThreadPool()
    sig = MySignals()
    acc_list_handler = AccListHandler()
    tray_icon = TrayIcon()
    tray_icon.show()
    w = Window()
    notify_service_running = True
    socket_listener_running = True


    def open_window():
        w.show()


    # noinspection PyUnresolvedReferences
    sig.showWindowRequested.connect(open_window)

    threadpool.start(SocketListener())
    threadpool.start(NotificationLookupService())

    if not sys.argv.__contains__("--no-window"):
        w.show()
    sys.exit(app.exec_())

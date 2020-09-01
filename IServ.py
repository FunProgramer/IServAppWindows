# -*- coding: utf-8 -*-
import http.client as httplib
import os
import sys
from time import sleep

import notify2
import requests
import simplejson
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QUrl, QDir, QThreadPool, QRunnable, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
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


# noinspection PyUnresolvedReferences
class Window(QtWidgets.QWidget, window.Ui_Window):
    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)
        self.stackedWidget.setCurrentWidget(self.loading_page)

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
        self.login_not_running = True

        self.download = None
        self.file = None

        self.webView.loadFinished.connect(self.load_finished)
        self.webView.urlChanged.connect(self.url_changed)

        self.webView.setPage(Page(self.webView))

        self.webView.page().profile().downloadRequested.connect(self.download_requested)

        # last_widget
        self.last_widget = self.account_page

        # NotificationLookupService
        self.threadpool.start(notify_service)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        # Splash Loading Screen
        sig.waitFinished.connect(self.wait_finished)
        self.info_label.setText("Bitte warten...")
        movie = QMovie(":/pictures/Loader.gif")
        self.loading_label.setMovie(movie)
        self.loading_label.movie().start()
        self.threadpool.start(SplashScreenLoader())

    # Key Press Event
    def keyPressEvent(self, key_event: QtGui.QKeyEvent) -> None:
        if key_event.key() == Qt.Key_Return and self.stackedWidget.currentWidget() == self.add_account_page:
            self.ok_clicked()

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
            # Get account information and save it in self.acc
            self.acc = acc_list_handler.get_login_data(index.row())

            # Show loading page and start loading the login page
            self.stackedWidget.setCurrentWidget(self.loading_page)
            self.last_widget = self.account_page

            self.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
            self.info_label.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")

    def add_acc_clicked(self):
        # Show add account page
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
        # Hide error message from before, when it is visible.
        self.error_label.hide()
        # Check if password is not empty and email is valid. If something from that is wrong show error message.
        if not str(self.email_lineEdit.text()).__contains__("@") \
                or not str(self.email_lineEdit.text()).__contains__("."):
            self.error_label.setText("Bitte geben Sie eine gültige IServ-Email-Adresse ein")
            self.error_label.show()
        elif not self.password_lineEdit.text():
            self.error_label.setText("Bitte geben Sie ein Passwort ein")
            self.error_label.show()
        # Check if an error is shown. If not add account.
        if not self.error_label.isVisible():
            uid = acc_list_handler.add_acc(self.email_lineEdit.text(), self.password_lineEdit.text())
            # Check if account was not added before. If not go into the if loop
            if not uid == -1:
                # Get account information and save it to self.uid and self.acc
                self.acc = acc_list_handler.get_login_data(uid)
                self.uid = uid
                # Start loading login page and show loading message
                self.last_widget = self.add_account_page
                self.stackedWidget.setCurrentWidget(self.loading_page)
                self.info_label.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")
                w.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
            # ^ Else go into the else loop.
            else:
                self.error_label.setText("Account wurde bereits hinzugefügt!")
                self.error_label.show()

    # web_view_page
    def load_finished(self, successful):
        # Check if page loading was successful. If not return to the account page and show error message
        if not successful:
            if self.last_widget == self.account_page:
                self.info_error_label.setText(
                    "Die Verbindung zum Server konnte nicht hergestellt werden oder wurde unterbrochen!")
                self.info_error_label.setStyleSheet("color: red")
                self.info_error_label.show()
            else:
                self.error_label.setText("Die Verbindung zum Server konnte nicht hergestellt werden oder wurde "
                                         "unterbrochen!")
                self.error_label.setStyleSheet("color: red")
                self.error_label.show()
                # If the account was just added and the internet connection is ok, delete the account.
                if have_internet():
                    acc_list_handler.delete_acc(self.uid)
            self.stackedWidget.setCurrentWidget(self.last_widget)
        # ^ Else go into the else loop
        else:
            # Check if login page was loaded and login isn't running. If that is right go into if loop.
            if self.webView.url().__eq__(
                    QUrl("https://" + self.acc["host"] + "/iserv/login")) & self.login_not_running:
                # Show loading info that login is running and save that login is running into self.login_not_running
                self.info_label.setText("Login für " + self.acc["email"] + " wird ausgeführt")
                self.login_not_running = False
                # Then fill the login form with the login information and submit it.
                self.webView.page().runJavaScript(
                    "document.getElementsByName('_username').item(0).value='" + self.acc["username"] + "'")
                self.webView.page().runJavaScript(
                    "document.getElementsByName('_password').item(0).value='" + self.acc["password"] + "'")
                self.webView.page().runJavaScript("document.forms[0].submit()")
            # ^ Else if loading the login page is finished again then something went wrong.
            # Show the user an error information and delete the account if it was just added.
            elif self.webView.url().__eq__(QUrl("https://" + self.acc["host"] + "/iserv/login")):
                if self.last_widget == self.acc_page:
                    self.error.setText("Login nicht erfolgreich")
                    self.error.show()
                    self.login_not_running = False
                else:
                    self.error_2.setText("Login nicht erfolgreich")
                    self.error_2.show()
                    acc_list_handler.delete_acc(self.uid)
                    self.login_not_running = False
                w.stackedWidget.setCurrentWidget(self.last_widget)
            # If the IServ Dashboard is finished loading we can show it to the user
            if self.webView.url() == QUrl("https://" + self.acc["host"] + "/iserv/"):
                self.stackedWidget.setCurrentWidget(self.webview_page)

    def url_changed(self, url):
        if url == QUrl("https://dbrs-gf.de/iserv/app/login") and not self.login_not_running:
            self.login_not_running = True
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
        # Start Worker1 on every url change

    def download_requested(self, download):
        self.stackedWidget.setCurrentWidget(self.webview_page)
        acc_list_handler.add_acc(self.acc["email"], self.acc["password"])
        self.info_error_label.clear()
        self.error_label.clear()
        # Get file name and change download path to /tmp/ and then the filename
        path = str(download.path()).split("/")
        file = path[len(path) - 1]
        download.setPath(self.tmpPath + file)
        # Save download object and filename to self.download and self.file
        self.download = download
        self.file = file

        # Accept download and connect download_finished
        download.accept()
        download.finished.connect(self.download_finished)

    def download_finished(self):
        # Determine os and start the the respective application
        if sys.platform == "win32":
            os.startfile(self.download.path())
        if sys.platform == "linux":
            os.system("xdg-open " + self.tmpPath + "'" + self.file + "'")

    # Boot Loading Screen
    def wait_finished(self):
        if not acc_list_handler.acc_list_exist():
            self.stackedWidget.setCurrentWidget(w.add_account_page)
            self.cancel_button.hide()
        else:
            self.stackedWidget.setCurrentWidget(w.account_page)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
        self.hide()
        if self.stackedWidget.currentWidget() == self.webview_page:
            self.webView.load(QUrl("http://" + self.acc["host"] + "/iserv/app/logout"))


def have_internet():
    # Check if internet connection is available with sending an request to google.com
    conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except OSError:
        conn.close()
        return False


class MySignals(QObject):
    waitFinished = pyqtSignal()


class SplashScreenLoader(QRunnable):
    def run(self) -> None:
        sleep(1)
        # noinspection PyUnresolvedReferences
        sig.waitFinished.emit()


class NotificationLookupService(QRunnable):
    def run(self) -> None:
        icon = "/opt/IServ/ICON.png"
        displayed_notifications = []
        global notify_service_running
        while notify_service_running:
            try:
                for acc in acc_list_handler.accList:
                    login_data = acc_list_handler.get_login_data(acc)
                    data = {
                        '_username': login_data["username"],
                        '_password': login_data["password"]
                    }
                    response = requests.post('https://' + login_data["host"] + '/iserv/app/login',
                                             params=(('target', '/iserv/user/api/notifications'),),
                                             data=data)
                    try:
                        notifications = response.json()['data']['notifications']
                    except KeyError:
                        continue
                    except simplejson.errors.JSONDecodeError:
                        continue
                    for notification in notifications:
                        if not displayed_notifications.__contains__(notification):
                            desktop_notification = notify2.Notification(notification['message'],
                                                                        notification['title'], icon)
                            desktop_notification.show()
                            displayed_notifications.append(notification)
            except RuntimeError:
                pass


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

    def was_activated(self, reason):
        if reason == QSystemTrayIcon.MiddleClick:
            self.exit()
        if reason == QSystemTrayIcon.Trigger:
            self.open_close()


if __name__ == "__main__":
    # If this is the main application, then:
    # - Create an QApplication
    # - Create an Window
    # - Show the Window
    # - and start the QEventLoop
    app = QApplication(sys.argv)
    tray_icon = TrayIcon()
    sig = MySignals()
    acc_list_handler = AccListHandler()
    notify2.init("IServ")
    notify_service_running = False
    notify_service = NotificationLookupService()
    tray_icon.show()
    w = Window()
    if not sys.argv.__contains__("--no-window"):
        w.show()
    sys.exit(app.exec_())

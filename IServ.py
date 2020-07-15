# -*- coding: utf-8 -*-
import http.client as httplib
import json
import os
import sys
from time import sleep

from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl, QDir, QThreadPool, QRunnable, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication

import MainView


# noinspection PyUnresolvedReferences
class MainWindow(QtWidgets.QMainWindow, MainView.Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.first_load = True

        # Account
        self.acc = None
        self.uid = None

        # Threads
        self.threadpool = QThreadPool()
        self.tmpPath = QDir.tempPath() + "/IServCache/"

        # acc_page
        self.update_acc_view()
        self.accView.clicked.connect(self.acc_clicked)
        self.addAcc.clicked.connect(self.add_acc_clicked)
        self.delAcc.setCheckable(True)

        # add_acc_page
        self.back.clicked.connect(self.back_clicked)
        self.OK_Button.clicked.connect(self.ok_clicked)

        # web_view_page
        self.login_not_running = True

        self.download = None
        self.file = None

        self.webView.loadFinished.connect(self.load_finished)
        self.webView.urlChanged.connect(self.url_changed)

        self.webView.page().profile().downloadRequested.connect(self.download_requested)

        # Boot Loading Screen
        sig.waitFinished.connect(self.wait_finished)
        self.loading_info.setText("Bitte warten ...")
        self.threadpool.start(Worker2())

    # acc_page
    def update_acc_view(self):
        for i in acc_list_handler.accList:
            self.accView.addItem(acc_list_handler.accList[i]["email"])

    def acc_clicked(self, index):
        if self.delAcc.isChecked():
            acc_list_handler.delete_acc(index.row())
            self.accView.clear()
            self.update_acc_view()
            if acc_list_handler.accList.__len__ == 0:
                self.stackedWidget.setCurrentWidget(self.add_acc_page)
                self.back.hide()
        else:
            # Get account information and save it in self.acc
            self.acc = acc_list_handler.get_login_data(index.row())

            # Show loading page and start loading the login page
            self.stackedWidget.setCurrentWidget(self.loading_page)
            self.stackedWidget.last = self.acc_page
            w.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
            self.loading_info.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")

    def add_acc_clicked(self):
        # Show add account page
        self.stackedWidget.setCurrentWidget(self.add_acc_page)
        self.stackedWidget.last = self.add_acc_page

    # add_acc_page
    def back_clicked(self):
        self.stackedWidget.setCurrentWidget(self.acc_page)

    def ok_clicked(self):
        # Hide error message from before, when it is visible.
        self.error_2.hide()
        # Check if password is not empty and email is valid. If something from that is wrong show error message.
        if not str(self.lineEdit.text()).__contains__("@") or not str(self.lineEdit.text()).__contains__("."):
            self.error_2.setText("Bitte geben Sie eine gültige IServ-Email-Adresse ein")
            self.error_2.show()
        elif not self.lineEdit_2.text():
            self.error_2.setText("Bitte geben Sie ein Passwort ein")
            self.error_2.show()
        # Check if an error is shown. If not add account.
        if not self.error_2.isVisible():
            uid = acc_list_handler.add_acc(self.lineEdit.text(), self.lineEdit_2.text())
            # Check if account was not added before. If not go into the if loop
            if not uid == -1:
                # Get account information and save it to self.uid and self.acc
                self.uid = uid
                self.acc = acc_list_handler.get_login_data(uid)
                # Start loading login page and show loading message
                self.stackedWidget.setCurrentWidget(self.loading_page)
                self.loading_info.setText("Verbindung zum Server " + self.acc["host"] + " wird hergestellt ...")
                w.webView.load(QUrl("https://" + self.acc["host"] + "/iserv/login"))
            # ^ Else go into the else loop.
            else:
                self.error_2.setText("Account wurde bereits hinzugefügt!")
                self.error_2.show()

    # web_view_page
    def load_finished(self, successful):
        # Check if page loading was successful. If not return to the account page and show error message
        if self.first_load:
            self.first_load = False
        if not successful and self.first_load:
            if self.stackedWidget.last == self.acc_page:
                self.error.setText("Die Verbindung zum Server konnte nicht hergestellt werden!")
                self.error.show()
            else:
                self.error_2.setText("Die Verbindung zum Server konnte nicht hergestellt werden!")
                self.error_2.show()
                # If the account was just added and the internet connection is ok, delete the account.
                if have_internet():
                    acc_list_handler.delete_acc(self.uid)
            self.stackedWidget.setCurrentWidget(self.stackedWidget.last)
        # ^ Else go into the else loop
        else:
            # Check if login page was loaded and login isn't running. If that is right go into if loop.
            if self.webView.url().__eq__(QUrl("https://" + self.acc["host"] + "/iserv/login")) & self.login_not_running:
                # Show loading info that login is running and save that login is running into self.login_not_running
                self.loading_info.setText("Login für " + self.acc["email"] + " wird ausgeführt")
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
                if self.stackedWidget.last == self.acc_page:
                    self.error.setText("Login nicht erfolgreich")
                    self.error.show()
                else:
                    self.error_2.setText("Login nicht erfolgreich")
                    self.error_2.show()
                    acc_list_handler.delete_acc(self.uid)
                w.stackedWidget.setCurrentWidget(w.stackedWidget.last)
            # If the IServ Dashboard is finished loading we can show it to the user
            if self.webView.url() == QUrl("https://" + self.acc["host"] + "/iserv/"):
                self.stackedWidget.setCurrentWidget(self.web_view_page)

    def url_changed(self, url):
        if url == QUrl("https://dbrs-gf.de/iserv/app/login") and not self.login_not_running:
            self.login_not_running = True
            self.back.show()
            self.accView.clear()
            self.update_acc_view()
            self.stackedWidget.setCurrentWidget(self.acc_page)
        # Start Worker1 on every url change
        worker = Worker1()
        self.threadpool.start(worker)

    def download_requested(self, download):
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
            self.stackedWidget.setCurrentWidget(w.add_acc_page)
            self.back.hide()
        else:
            self.stackedWidget.setCurrentWidget(w.acc_page)


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


class Worker1(QRunnable):
    def run(self) -> None:
        # Wait an half second and then delete all targets in any link
        sleep(0.5)
        w.webView.page().runJavaScript("for (var i = 0; i < document.links.length; i++) "
                                       "{document.links.item(i).target = ''}")


class Worker2(QRunnable):
    def run(self) -> None:
        # Wait 1 second and then show account page
        sleep(1)
        # noinspection PyUnresolvedReferences
        sig.waitFinished.emit()


class AccListHandler:
    def __init__(self):
        super().__init__()
        self.acc_list_path = str(QDir.homePath()) + "/IServAcc"
        self.accList = {}
        if self.acc_list_exist():
            with open(self.acc_list_path, "r") as accListJson:
                self.accList = json.loads(accListJson.read())

    def save_acc_list(self):
        # Open IServAcc file save accList to it
        with open(self.acc_list_path, "w") as accListJson:
            accListJson.write(json.dumps(self.accList))

    def get_login_data(self, uid):
        # Read account information from accList and return them
        login_data = self.accList[str(uid)]
        return login_data

    def add_acc(self, email, password):
        # Check if account is already added
        for acc in self.accList:
            if self.accList[acc]["email"] == email:
                return -1
        # Create new uid for new account
        uid = self.accList.__len__()
        # add account to accList
        self.accList.update({str(uid): {"username": str(email).split("@", 2).__getitem__(0),
                                        "host": str(email).split("@", 2).__getitem__(1),
                                        "email": email,
                                        "password": password}})
        # Call save_acc_list for update the IServAcc file with the new account
        self.save_acc_list()

        # Return new uid
        return uid

    def delete_acc(self, uid):
        # Delete the account from accList and update IServAcc
        del self.accList[str(uid)]
        self.save_acc_list()

    def acc_list_exist(self):
        # Check if IServAcc exists and is not containing an account
        if os.path.exists(self.acc_list_path):
            # with open(self.acc_list_path, "w") as accListJson:
            if not json.loads(open(self.acc_list_path).read()).__len__() == 0:
                return True
            else:
                return False
        else:
            return False


if __name__ == "__main__":
    # If this is the main application, then:
    # - Create an QApplication
    # - Create an MainWindow
    # - Show the MainWindow
    # - and start the QEventLoop
    app = QApplication(sys.argv)
    sig = MySignals()
    acc_list_handler = AccListHandler()
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

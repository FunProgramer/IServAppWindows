# -*- coding: utf-8 -*-
import json
import os
import sys
from time import sleep

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QUrl, QDir, QThreadPool, QRunnable

import AccWindow
import AddAccWindow
import Webview


def acc_list_exist():
    if os.path.exists(accListPath):
        if not os.stat(accListPath).st_size == 0:
            return True
        else:
            return False
    else:
        return False


class AccListHandler:
    def __init__(self):
        super().__init__()
        if acc_list_exist():
            with open(accListPath, "r") as accListJson:
                self.accList = json.loads(accListJson.read())
        else:
            self.accList = {}

    def save_acc_list(self):
        with open(accListPath, "w") as accListJson:
            accListJson.write(json.dumps(self.accList))

    def get_login_data(self, account_id):
        login_data = self.accList[str(account_id)]
        return login_data

    def add_acc(self, email, password):
        if aaw.mode == "first_run":
            self.accList.update({str(0): {"email": email, "password": password}})
        else:
            self.accList.update({str(self.accList.__sizeof__() + 1): {"email": email, "password": password}})
        self.save_acc_list()


class MainWindow(QtWidgets.QMainWindow, Webview.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.webView.loadFinished.connect(self.load_finished)
        self.webView.urlChanged.connect(self.url_changed)
        self.webView.page().profile().downloadRequested.connect(self.download_requested)
        self.login = False
        self.threadPool = QThreadPool()
        self.download_path = None
        self.download_type = None
        self.host = None

    def download_requested(self, download):
        self.download_type = str(download.path()).split(".", 2).__getitem__(1)
        tmp_file = tmpPath + "/IServFile"
        download.setPath(tmp_file + "." + self.download_type)

        download.accept()
        download.finished.connect(self.download_finished)
        print(download.path())
        self.download_path = download.path()

    def download_finished(self):
        print("finished")
        if sys.platform == "win32":
            os.startfile(self.download_path)
        if sys.platform == "linux":
            if str(self.download_type) == "docx":
                os.system("libreoffice " + self.download_path)
            else:
                os.system("xdg-open " + self.download_path)

    def url_changed(self):
        print(self.webView.url())
        if not self.webView.url() == QUrl.fromLocalFile(QDir().current().filePath("splash.html")):
            worker = Worker()
            self.threadPool.start(worker)

    def load_finished(self):
        if self.webView.url() == QUrl.fromLocalFile(QDir().current().filePath("splash.html")):
            prepare_login()
        elif self.webView.url() == QUrl("https://" + str(self.login_data["email"]).split("@", 2)[1] + "/iserv/login")\
                and self.login:
            self.webView.page().runJavaScript(
                "document.getElementById('username').value='" + str(self.login_data["email"]).split("@", 2)[0] + "'")
            self.webView.page().runJavaScript(
                "document.getElementById('password').value='" + self.login_data["password"] + "'")
            self.webView.page().runJavaScript("document.forms[0].submit()")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if aaw.isVisible():
            aaw.close()
        if aw.isVisible():
            aw.close()
        app.exit(0)


class Worker(QRunnable):
    def run(self) -> None:
        sleep(0.5)
        w.webView.page().runJavaScript("for (var i = 0; i < document.links.length; i++) {document.links.item("
                                       "i).target = ''}")


class AccWindowHandler(QtWidgets.QWidget, AccWindow.Ui_Form):
    def __init__(self, parent=None):
        super(AccWindowHandler, self).__init__(parent)
        self.setupUi(self)
        self.accView.clicked.connect(self.acc_clicked)
        self.addAcc.clicked.connect(self.add_acc_clicked)
        for i in AccListHandler().accList:
            self.accView.addItem(AccListHandler().accList[i]["email"])

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        app.exit(0)

    def update_acc_view(self):
        self.accView.clear()
        for i in AccListHandler().accList:
            self.accView.addItem(AccListHandler().accList[i]["username"])

    def acc_clicked(self):
        login(self.accView.row(self.accView.currentItem()))
        self.hide()

    @staticmethod
    def add_acc_clicked():
        aaw.show()


class AddAccWindowHandler(QtWidgets.QWidget, AddAccWindow.Ui_Form):
    def __init__(self, parent=None):
        super(AddAccWindowHandler, self).__init__(parent)
        self.setupUi(self)
        self.mode = str()
        self.Cancel_Button.clicked.connect(self.cancel)
        self.OK_Button.clicked.connect(self.ok)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.mode == "first_run":
            app.exit(0)

    def cancel(self):
        if self.mode == "first_run":
            sys.exit(0)
        else:
            self.hide()

    def ok(self):
        AccListHandler().add_acc(self.lineEdit.text(), self.lineEdit_2.text())
        self.hide()
        if self.mode == "first_run":
            login(0)
        else:
            aw.update_acc_view()


def main():
    w.show()
    sys.exit(app.exec_())


def prepare_login():
    # Automatic Login

    if acc_list_exist():
        aw.show()
    else:
        aaw.mode = "first_run"
        aaw.show()


def login(count: int):
    login_data = AccListHandler().get_login_data(count)

    w.webView.load(QUrl("https://" + str(login_data["email"]).split("@", 2)[1] + "/iserv/login"))
    w.login = True
    w.login_data = login_data


if __name__ == "__main__":
    accListPath = str(QDir.homePath()) + "/IServAcc"
    tmpPath = str(QDir.tempPath()) + "/IServAppCache"
    if not QDir(tmpPath).exists():
        QDir().mkdir(tmpPath)

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    aw = AccWindowHandler()
    aaw = AddAccWindowHandler()
    main()

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AddAcc.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(350, 176)
        Form.setMinimumSize(QtCore.QSize(350, 176))
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(Form)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(Form)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.verticalLayout.addWidget(self.lineEdit_2)
        self.widget = QtWidgets.QWidget(Form)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.Cancel_Button = QtWidgets.QPushButton(self.widget)
        self.Cancel_Button.setObjectName("Cancel_Button")
        self.horizontalLayout.addWidget(self.Cancel_Button)
        self.OK_Button = QtWidgets.QPushButton(self.widget)
        self.OK_Button.setObjectName("OK_Button")
        self.horizontalLayout.addWidget(self.OK_Button)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.lineEdit, self.lineEdit_2)
        Form.setTabOrder(self.lineEdit_2, self.Cancel_Button)
        Form.setTabOrder(self.Cancel_Button, self.OK_Button)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Login"))
        self.label.setText(_translate("Form", "IServ Email"))
        self.lineEdit.setPlaceholderText(_translate("Form", "vorname.nachname@iserv"))
        self.label_2.setText(_translate("Form", "Password"))
        self.lineEdit_2.setPlaceholderText(_translate("Form", "********"))
        self.Cancel_Button.setText(_translate("Form", "Abbrechen"))
        self.OK_Button.setText(_translate("Form", "OK"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())


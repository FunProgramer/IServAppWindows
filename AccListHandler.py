# -*- coding: utf-8 -*-
import json
import os

from PyQt5.QtCore import QDir


class AccListHandler:
    def __init__(self):
        super().__init__()
        self.acc_list_path = str(QDir.homePath()) + "/AppData/Roaming/IServ/IServAcc"
        self.accList = []
        if self.acc_list_exist():
                with open(self.acc_list_path, "r") as accListJson:
                    self.accList = json.loads(accListJson.read())

    def save_acc_list(self):
        try:
            with open(self.acc_list_path, "w") as accListJson:
                accListJson.write(json.dumps(self.accList))
        except FileNotFoundError:
            os.makedirs(str(QDir.homePath()) + "/AppData/Roaming/IServ/")
            pass

    def get_login_data(self, uid):
        # Read account information from accList and return them
        login_data = self.accList[uid]
        return login_data

    def add_acc(self, email, password):
        # Check if account is already added
        for acc in self.accList:
            if acc["email"] == email:
                return -1
        # Create new msg_list for new account
        uid = self.accList.__len__()
        # add account to accList
        self.accList.append({"username": str(email).split("@", 2).__getitem__(0),
                             "host": str(email).split("@", 2).__getitem__(1),
                             "email": email,
                             "password": password})
        # Call save_acc_list for update the IServAcc file with the new account
        self.save_acc_list()

        # Return new msg_list
        return uid

    def delete_acc(self, uid):
        # Delete the account from accList and update IServAcc
        del self.accList[uid]
        self.save_acc_list()

    def acc_list_exist(self):
        # Check if IServAcc exists and is containing an account
        if os.path.exists(self.acc_list_path):
            if not json.loads(open(self.acc_list_path).read()).__len__() == 0:
                return True
            else:
                return False
        else:
            return False

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'valhalla/gui/ValhallaLocateDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_VahallaLocateDialog(object):
    def setupUi(self, VahallaLocateDialog):
        VahallaLocateDialog.setObjectName("VahallaLocateDialog")
        VahallaLocateDialog.resize(400, 522)
        self.verticalLayout = QtWidgets.QVBoxLayout(VahallaLocateDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.locate_text = QtWidgets.QTextBrowser(VahallaLocateDialog)
        self.locate_text.setObjectName("locate_text")
        self.verticalLayout.addWidget(self.locate_text)
        self.locate_buttons = QtWidgets.QDialogButtonBox(VahallaLocateDialog)
        self.locate_buttons.setOrientation(QtCore.Qt.Horizontal)
        self.locate_buttons.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.locate_buttons.setObjectName("locate_buttons")
        self.verticalLayout.addWidget(self.locate_buttons)

        self.retranslateUi(VahallaLocateDialog)
        self.locate_buttons.accepted.connect(VahallaLocateDialog.accept) # type: ignore
        self.locate_buttons.rejected.connect(VahallaLocateDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(VahallaLocateDialog)

    def retranslateUi(self, VahallaLocateDialog):
        _translate = QtCore.QCoreApplication.translate
        VahallaLocateDialog.setWindowTitle(_translate("VahallaLocateDialog", "Locate Response"))
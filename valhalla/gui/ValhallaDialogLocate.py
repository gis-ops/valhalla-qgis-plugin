# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                 Valhalla - QGIS plugin
 QGIS client to query Valhalla APIs
                              -------------------
        begin                : 2019-10-12
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Nils Nolde
        email                : nils@gis-ops.com
 ***************************************************************************/

 This plugin provides access to some of the APIs from Valhalla
 (https://github.com/valhalla/valhalla), developed and
 maintained by https://gis-ops.com, Berlin, Germany.

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

from .ValhallaLocateDialog import Ui_VahallaLocateDialog


class ValhallaDialogLocateMain(QDialog, Ui_VahallaLocateDialog):
    """Builds provider config dialog."""

    responseArrived = pyqtSignal(str)

    def __init__(self, parent=None):
        """
        :param parent: Parent window for modality.
        :type parent: QDialog
        """
        QDialog.__init__(self, parent)

        self.setupUi(self)

        # Setup signal
        self.responseArrived.connect(self.print_response)

    def print_response(self, text):
        """
        Slot to print response to text box.

        :param text: The text to be output in the QTextBrowser
        :type text: str
        """
        self.locate_text.setText(text)

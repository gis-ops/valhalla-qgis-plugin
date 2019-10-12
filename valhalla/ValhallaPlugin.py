# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                 Valhalla - QGIS plugin
 QGIS client to query Valhalla APIs
                              -------------------
        begin                : 2019-10-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Nils Nolde
        email                : nils@gis-ops.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
 this plugin you agree to the ORS terms of service
 (https://openrouteservice.org/terms-of-service/).

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import QgsApplication

from .gui import ValhallaDialog
from .proc import provider


class Valhalla():
    """QGIS Plugin Implementation."""
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.dialog = ValhallaDialog.ValhallaDialogMain(iface)
        self.provider = provider.ValhallaProvider()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        QgsApplication.processingRegistry().addProvider(self.provider)
        self.dialog.initGui()
        
    def unload(self):
        """remove menu entry and toolbar icons"""
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.dialog.unload()
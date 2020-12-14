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

from qgis.core import QgsMessageLog, Qgis

from valhalla import PLUGIN_NAME

def log(message, level_in=0):
    """
    Writes to QGIS inbuilt logger accessible through panel.

    :param message: logging message to write, error or URL.
    :type message: str

    :param level_in: integer representation of logging level.
    :type level_in: int
    """
    if level_in == 0:
        level = Qgis.Info
    elif level_in == 1:
        level = Qgis.Warning
    elif level_in == 2:
        level = Qgis.Critical
    else:
        level = Qgis.Info

    QgsMessageLog.logMessage(message, PLUGIN_NAME.strip(), level)
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
from PyQt5.QtGui import QColor

from qgis.core import (QgsWkbTypes)
from qgis.gui import (QgsMapToolEmitPoint,
                      QgsRubberBand)

from valhalla_qgis_plugin import DEFAULT_COLOR


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, canvas):
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.crsSrc = self.canvas.mapSettings().destinationCrs()
        self.previous_point = None
        self.points = []
        self.reset()

    def reset(self):
        """reset rubberband and captured points."""

        self.points = []

    pointDrawn = pyqtSignal(["QgsPointXY", "int"])
    def canvasReleaseEvent(self, e):
        """Add marker to canvas and shows line."""
        new_point = self.toMapCoordinates(e.pos())
        self.points.append(new_point)

        self.pointDrawn.emit(new_point, self.points.index(new_point))

    doubleClicked = pyqtSignal()
    def canvasDoubleClickEvent(self, e):
        """Ends line drawing and deletes rubberband and markers from map canvas."""
        self.doubleClicked.emit()

    def deactivate(self):
        super(LineTool, self).deactivate()
        self.deactivated.emit()

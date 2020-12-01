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

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject
                       )


def transformToWGS(old_crs):
    """
    Returns a transformer to WGS84

    :param old_crs: CRS to transfrom from
    :type old_crs: QgsCoordinateReferenceSystem

    :returns: transformer to use in various modules.
    :rtype: QgsCoordinateTransform
    """
    outCrs = QgsCoordinateReferenceSystem('EPSG:4326')
    xformer = QgsCoordinateTransform(old_crs, outCrs, QgsProject.instance())

    return xformer

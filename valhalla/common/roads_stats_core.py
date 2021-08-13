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

from typing import List
import json
from PyQt5.QtCore import QVariant

from qgis.core import (QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields,
                       QgsField)

from valhalla.utils import convert


def get_fields():
    """
    Builds output fields for directions response layer.

    :param line: Specifies whether the output feature is a line or a point
    :type line: boolean

    :returns: fields object to set attributes of output layer
    :rtype: QgsFields
    """

    # the field names correspond with the GeoJSON response field names
    fields = QgsFields()
    fields.append(QgsField("MAX_GRADE", QVariant.Int))
    # fields.append(QgsField("MAX_DOWN_GRADES", QVariant.Int))
    fields.append(QgsField("MEAN_ELEVATION", QVariant.Int))
    fields.append(QgsField("MAX_SPEED", QVariant.Int))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("OPTIONS", QVariant.String))

    return fields


def get_output_features_roads_stats(response, profile, options=None, group_grades=False) -> List[QgsFeature]:
    feats = list()
    props = response['features'][0]['properties']
    if not group_grades:
        for idx, coords in enumerate(response['features'][0]['geometry']['coordinates']):
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in coords]))
            attrs = [props[f.name().lower()][idx] for f in get_fields().toList()[:-2]]
            attrs.extend([profile, json.dumps(options)])
            feat.setAttributes(attrs)

            feats.append(feat)
    else:
        # TODO: add MultiLineString, one feature per grade bucket
        pass

    return feats

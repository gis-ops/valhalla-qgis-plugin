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

from ..utils import convert


def get_fields():
    """
    Builds output fields for directions response layer.

    :param line: Specifies whether the output feature is a line or a point
    :type line: boolean

    :returns: fields object to set attributes of output layer
    :rtype: QgsFields
    """

    fields = QgsFields()
    fields.append(QgsField("ID", QVariant.Int))
    fields.append(QgsField("DIST_KM", QVariant.Double))
    fields.append(QgsField("DURATION_H", QVariant.Double))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("OPTIONS", QVariant.String))

    return fields


def get_output_feature_gravity(response, profile, options=None):
    """
    Build output feature based on response attributes for directions endpoint.

    :param response: API response object
    :type response: dict

    :param profile: Transportation mode being used
    :type profile: str

    :param options: Costing option being used.
    :type options: dict

    :returns: Output trip and gravity point features with attributes and geometry set.
    :rtype: List[QgsFeature]
    """
    trips = [response['trip']]
    for t in response['alternates']:
        trips.append(t['trip'])

    route_feats = []
    total_dist, total_time = 0, 0
    point_feat = QgsFeature()
    for idx, trip in enumerate(trips):
        feat = QgsFeature()
        coordinates, distance, duration = [], 0, 0
        for leg in trip['legs']:
            coordinates.extend([
                list(reversed(coord))
                for coord in convert.decode_polyline6(leg['shape'])
            ])
            duration += round(leg['summary']['time'] / 3600, 3)
            distance += round(leg['summary']['length'], 3)

            total_dist += distance
            total_time += duration

            qgis_coords = [QgsPointXY(x, y) for x, y in coordinates]
            feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
            feat.setAttributes([
                idx,
                distance,
                duration,
                profile,
                json.dumps(options)
            ])

            route_feats.append(feat)

        # get point feature
        point_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*coordinates[-1])))
        point_feat.setAttributes([
            0,
            total_dist,
            total_time,
            profile,
            json.dumps(options)
        ])

    return route_feats, point_feat

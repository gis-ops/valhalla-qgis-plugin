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
from typing import Tuple, List

from PyQt5.QtCore import QVariant
from qgis._core import QgsPointXY, QgsGeometry
from qgis.core import QgsFields, QgsField, QgsFeature

from ..utils.convert import decode_polyline6


def get_fields(t: str) -> QgsFields:
    """
    Returns the fields for trace_attributes depending on type of layer.

    :param t: edge or point
    :returns: initialized QgsFields object
    """


    fields = QgsFields()
    if t == 'edge':
        fields.append(QgsField("EDGE_ID", QVariant.Double))
        fields.append(QgsField("OSM_ID", QVariant.Double))
        fields.append(QgsField("SPEED", QVariant.Int))
        fields.append(QgsField("LENGTH", QVariant.Double))
        fields.append(QgsField("MEAN_ELEVATION", QVariant.Int))
        fields.append(QgsField("SRC_PERC", QVariant.Double))
        fields.append(QgsField("TARGET_PERC", QVariant.Double))
    else:
        fields.append(QgsField("TYPE", QVariant.String))
        fields.append(QgsField("EDGE_INDEX", QVariant.Double))
        fields.append(QgsField("DIST_ALONG_EDGE", QVariant.Double))
        fields.append(QgsField("DIST_TO_INPUT", QVariant.Double))

    return fields


def get_output_features(response: dict) -> Tuple[List[QgsFeature], List[QgsFeature]]:
    """
    Returns the line & point features
    """
    edge_feats, point_feats = [], []

    shape_pts = [list(reversed(coord)) for coord in decode_polyline6(response['shape'])]

    for edge in response['edges']:
        feat = QgsFeature()
        coords = [QgsPointXY(x, y) for x, y in shape_pts[edge['begin_shape_index'] : edge['end_shape_index'] + 1]]
        feat.setGeometry(QgsGeometry.fromPolylineXY(coords))
        feat.setAttributes([
            edge['id'],
            edge['way_id'],
            edge['speed'],
            edge['length'],
            edge.get('mean_elevation'),
            edge.get('source_percent_along'),
            edge.get('target_percent_along')
        ])
        edge_feats.append(feat)

    for point in response['matched_points']:
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point['lon'], point['lat'])))
        feat.setAttributes([
            point['type'],
            point.get('edge_index') or 0,
            point.get('distance_along_edge') or 0,
            point.get('distance_from_trace_point') or 0,
        ])
        point_feats.append(feat)

    return edge_feats, point_feats

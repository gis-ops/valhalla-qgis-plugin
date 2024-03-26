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

import json
from PyQt5.QtCore import QVariant

from qgis.core import (QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsPointXY,
                       QgsGeometry)

from valhalla.utils import convert, logger


def get_fields(from_type=QVariant.String, to_type=QVariant.String, from_name="FROM_ID", to_name="TO_ID"):
    """
    Builds output fields for directions response layer.

    :param from_type: field type for 'FROM_ID' field
    :type from_type: QVariant enum

    :param to_type: field type for 'TO_ID' field
    :type to_type: QVariant enum

    :param from_name: field name for 'FROM_ID' field
    :type from_name: str

    :param to_name: field name for 'TO_ID' field
    :type to_name: field name for 'TO_ID' field

    :returns: fields object to set attributes of output layer
    :rtype: QgsFields
    """

    fields = QgsFields()
    fields.append(QgsField(from_name, from_type))
    fields.append(QgsField(to_name, to_type))
    fields.append(QgsField("DIST_KM", QVariant.Double))
    fields.append(QgsField("DURATION_H", QVariant.Double))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("OPTIONS", QVariant.String))

    return fields


def get_output_features_matrix(response, profile, options={}, matrix_geometries=False, source_attrs=[], destination_attrs=[]):
    """
    Build output feature based on response attributes for directions endpoint.

    :param response: API response object
    :type response: dict

    :param profile: Transportation mode being used
    :type profile: str

    :param options: Costing options being used.
    :type options: dict

    :param matrix_geometries: Whether we want geometries for each connection.
    :type matrix_geometries: bool

    :param source_attrs: Attribute values of the source features.
    :type source_attrs: list of any

    :param destination_attrs: Attribute values of the destination features.
    :type destination_attrs: list of any

    :returns: Output features with attributes and geometry set.
    :rtype: list of QgsFeature
    """

    feats = []
    sources = response['sources']
    targets = response['targets']
    for o, origin in enumerate(response['sources_to_targets']):
        try:
            from_id = source_attrs[o]
        except IndexError:
            from_id ="{}, {}".format(sources[o]['lon'], sources[o]["lat"])
        for d, destination in enumerate(origin):
            try:
                to_id = destination_attrs[d]
            except IndexError:
                to_id ="{}, {}".format(targets[d]['lon'], targets[d]["lat"])
            time = destination['time']
            distance = destination['distance']

            if time:
                time = round(time / 3600, 3)
            if distance:
                distance = round(distance, 3)

            feat = QgsFeature()
            feat.setAttributes([
                from_id,
                to_id,
                distance,
                time,
                profile,
                json.dumps(options),
                ]
            )
            if matrix_geometries and destination.get("shape"):
                shape = destination.get("shape", "")
                qgis_coords = [QgsPointXY(x, y) for y, x in convert.decode_polyline6(shape)]
                feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
            feats.append(feat)

    return feats

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

from itertools import product
import json
from PyQt5.QtCore import QVariant

from qgis.core import (QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields,
                       QgsField)

from ..utils import convert


def get_request_point_features(route_dict, row_by_row):
    """
    Processes input point features depending on the layer to layer relation in directions settings

    :param route_dict: all coordinates and ID field values of start and end point layers
    :type route_dict: dict

    :param row_by_row: Specifies whether row-by-row relation or all-by-all has been used.
    :type row_by_row: str

    :returns: tuple of coordinates and ID field value for each routing feature in route_dict
    :rtype: tuple of QgsPointXY and others
    """

    locations_list = list(product(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))
    values_list = list(product(route_dict['start']['values'],
                               route_dict['end']['values']))

    # If row-by-row in two-layer mode, then only zip the locations
    if row_by_row == 'Row-by-Row':
        locations_list = list(zip(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))

        values_list = list(zip(route_dict['start']['values'],
                               route_dict['end']['values']))

    for properties in zip(locations_list, values_list):
        # Skip if first and last location are the same
        if properties[0][0] == properties[0][-1]:
            continue

        coordinates = [QgsPointXY(x, y) for x, y in properties[0]]
        values = properties[1]

        yield (coordinates, values)


def get_fields(from_type=QVariant.String, to_type=QVariant.String, from_name="FROM_ID", to_name="TO_ID", line=False):
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

    :param line: Specifies whether the output feature is a line or a point
    :type line: boolean

    :returns: fields object to set attributes of output layer
    :rtype: QgsFields
    """

    fields = QgsFields()
    fields.append(QgsField("DIST_KM", QVariant.Double))
    fields.append(QgsField("DURATION_H", QVariant.Double))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("OPTIONS", QVariant.String))
    fields.append(QgsField(from_name, from_type))
    if not line:
        fields.append(QgsField(to_name, to_type))

    return fields


def get_output_feature_directions(response, profile, options=None, from_value=None, to_value=None):
    """
    Build output feature based on response attributes for directions endpoint.

    :param response: API response object
    :type response: dict

    :param profile: Transportation mode being used
    :type profile: str

    :param options: Costing option being used.
    :type options: dict

    :param from_value: value of 'FROM_ID' field
    :type from_value: any

    :param to_value: value of 'TO_ID' field
    :type to_value: any

    :returns: Ouput feature with attributes and geometry set.
    :rtype: QgsFeature
    """
    response_mini = response['trip']
    feat = QgsFeature()
    coordinates, distance, duration = [], 0, 0
    for leg in response_mini['legs']:
            coordinates.extend([
                list(reversed(coord))
                for coord in convert.decode_polyline6(leg['shape'])
            ])
            duration += round(leg['summary']['time'] / 3600, 3)
            distance += round(leg['summary']['length'], 3)

    qgis_coords = [QgsPointXY(x, y) for x, y in coordinates]
    feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
    feat.setAttributes([distance,
                        duration,
                        profile,
                        json.dumps(options),
                        from_value,
                        to_value
                        ])

    return feat

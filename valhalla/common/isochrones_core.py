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

import json

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from qgis.core import (QgsPointXY,
                       QgsMultiPoint,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer)

class Isochrones():
    """convenience class to build isochrones"""

    def __init__(self):

        # Will all be set in self.set_parameters(), bcs Processing Algo has to initialize this class before it
        # knows about its own parameters
        self.profile = None
        self.geometry = None
        self.id_field_type = None
        self.id_field_name = None
        self.response = None

    def set_parameters(self, profile, geometry_param='LineString', id_field_type=QVariant.String, id_field_name='ID'):
        """
        Sets all parameters defined in __init__, because processing algorithm calls this class when it doesn't know its parameters yet.

        :param profile: Transportation mode being used
        :type profile: str

        :param geometry_param: geometry parameter for Valhalla isochrone service.
        :type geometry_param: str

        :param id_field_type: field type of ID field
        :type id_field_type: QVariant enum

        :param id_field_name: field name of ID field
        :type id_field_name: str
        """
        self.profile = profile
        self.geometry = geometry_param
        self.id_field_type = id_field_type
        self.id_field_name = id_field_name

    def set_response(self, response):
        """
        Set response to avoid passing it to every function

        :param response: The GeoJSON response
        :type response: dict
        """
        self.response = response

    def get_fields(self):
        """
        Set all fields for output isochrone layer.

        :returns: Fields object of all output fields.
        :rtype: QgsFields
        """
        fields = QgsFields()
        fields.append(QgsField(self.id_field_name, self.id_field_type))  # ID field
        fields.append(QgsField('contour', QVariant.Int))  # Dimension field
        fields.append(QgsField("profile", QVariant.String))
        fields.append(QgsField('options', QVariant.String))

        return fields

    def get_point_fields(self):
        """
        Set all fields for the output point layer.

        :returns: Point output fields.
        :rtype: QgsFields
        """
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.String))
        fields.append(QgsField("type", QVariant.String))

        return fields

    def get_features(self, id_field_value, options={}):
        """
        Generator to return output isochrone features from response.

        :param id_field_value: Value of ID field.
        :type id_field_value: any

        :param options: costing options
        :type options: dict

        :returns: output feature
        :rtype: QgsFeature
        """

        features = [feature for feature in self.response['features'] if feature['geometry']['type'] in ('LineString', 'Polygon')]

        # Sort features based on the isochrone value, so that longest isochrone
        # is added first. This will plot the isochrones on top of each other.
        l = lambda x: x['properties']['contour']
        for isochrone in sorted(features, key=l, reverse=True):
            feat = QgsFeature()
            coordinates = isochrone['geometry']['coordinates']
            iso_value = isochrone['properties']['contour']
            if self.geometry == 'Polygon':
                qgis_coords = [[QgsPointXY(coord[0], coord[1]) for coord in coordinates[0]]]
                feat.setGeometry(QgsGeometry.fromPolygonXY(qgis_coords))
            if self.geometry == 'LineString':
                qgis_coords = [QgsPointXY(coord[0], coord[1]) for coord in coordinates]
                feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
            feat.setAttributes([
                id_field_value,
                int(iso_value),
                self.profile,
                json.dumps(options)
            ])

            yield feat

    def get_multipoint_features(self, id_field_value):
        """
        Generator to return isochrone snapped locations from response.

        :param id_field_value: Value of ID field.
        :type id_field_value: any

        :returns: output feature
        :rtype: QgsFeature
        """
        multipoints = [feature for feature in self.response['features'] if feature['geometry']['type'] == 'MultiPoint']
        for multipoint in multipoints:
            feat = QgsFeature()
            coords = [QgsPointXY(*coords) for coords in multipoint['geometry']['coordinates']]
            feat.setGeometry(QgsGeometry.fromMultiPointXY(coords))
            feat.setAttributes([
                id_field_value,
                multipoint['properties']['type']
            ])

            yield feat

    def get_point_features(self, id_field_value):
        """
        Generator to return isochrone input locations from response.

        :param id_field_value: Value of ID field.
        :type id_field_value: any

        :returns: output feature
        :rtype: QgsFeature
        """
        points = [feature for feature in self.response['features'] if feature['geometry']['type'] == 'Point']
        for point in points:
            feat = QgsFeature()
            coords = QgsPointXY(*point['geometry']['coordinates'])
            feat.setGeometry(QgsGeometry.fromPointXY(coords))
            feat.setAttributes([
                id_field_value,
                point['properties']['type']
            ])

            yield feat

    def stylePoly(self, layer):
        """
        Style isochrone polygon layer.

        :param layer: Polygon layer to be styled.
        :type layer: QgsMapLayer
        """

        field = layer.fields().lookupField('contour')
        unique_values = sorted(layer.uniqueValues(field))

        colors = {0: QColor('#2b83ba'),
                  1: QColor('#64abb0'),
                  2: QColor('#9dd3a7'),
                  3: QColor('#c7e9ad'),
                  4: QColor('#edf8b9'),
                  5: QColor('#ffedaa'),
                  6: QColor('#fec980'),
                  7: QColor('#f99e59'),
                  8: QColor('#e85b3a'),
                  9: QColor('#d7191c')}

        categories = []

        for cid, unique_value in enumerate(unique_values):
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = QgsSimpleFillSymbolLayer(color=colors[cid],
                                                    strokeColor=QColor('#000000'))

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value) + ' mins')
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer('contour', categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setOpacity(0.5)

        layer.triggerRepaint()

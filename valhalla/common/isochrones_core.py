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
from PyQt5.QtGui import QColor

from qgis.core import (QgsPointXY,
                       QgsVectorLayer,
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

    def set_parameters(self, profile, geometry_param='Polygon', id_field_type=QVariant.String, id_field_name='ID'):
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
        fields.append(QgsField('metric', QVariant.String))

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

        features = [feature for feature in self.response['features'] if feature['geometry']['type'] in ('LineString', 'Polygon', 'MultiPolygon')]
        # Sort features based on the isochrone value, so that longest isochrone
        # is added first. This will plot the isochrones on top of each other.
        l = lambda x: x['properties']['contour']
        for isochrone in sorted(features, key=l, reverse=True):
            feat = QgsFeature()
            coordinates = isochrone['geometry']['coordinates']
            geom_type = isochrone['geometry']['type']
            iso_value = isochrone['properties']['contour']
            qgis_coords = []
            if geom_type == 'Polygon':
                for ring in coordinates:
                    ring_coords = []
                    for coord in ring:
                        ring_coords.append(QgsPointXY(coord[0], coord[1]))
                    qgis_coords.append(ring_coords)
                feat.setGeometry(QgsGeometry.fromPolygonXY(qgis_coords))
            if geom_type == 'LineString':
                qgis_coords = [QgsPointXY(coord[0], coord[1]) for coord in coordinates]
                feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
            if geom_type == 'MultiPolygon':
                for poly in coordinates:
                    poly_coords = []
                    for ring in poly:
                        ring_coords = []
                        for coord in ring:
                            ring_coords.append(QgsPointXY(coord[0], coord[1]))
                        poly_coords.append(ring_coords)
                    qgis_coords.append(poly_coords)
                feat.setGeometry(QgsGeometry.fromMultiPolygonXY(qgis_coords))

            feat.setAttributes([
                id_field_value,
                float(iso_value),
                self.profile,
                json.dumps(options),
                'time'
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

    def stylePoly(self, layer, metric: str):
        """
        Style isochrone polygon layer.

        :param QgsVectorLayer layer: Polygon layer to be styled.
        :param str metric: distance or time.
        """
        field = layer.fields().lookupField('contour')
        unique_values = sorted(layer.uniqueValues(field))

        colors = {
            "distance": {
                0: QColor('#FCF0EE'),
                1: QColor('#F9E1DC'),
                2: QColor('#F6D2CB'),
                3: QColor('#F3C3BA'),
                4: QColor('#F0B3A8'),
                5: QColor('#EDA396'),
                6: QColor('#EA9485'),
                7: QColor('#E78573'),
                8: QColor('#E47662'),
                9: QColor('#E16651')
            },
            "time": {
                0: QColor('#2b83ba'),
                1: QColor('#64abb0'),
                2: QColor('#9dd3a7'),
                3: QColor('#c7e9ad'),
                4: QColor('#edf8b9'),
                5: QColor('#ffedaa'),
                6: QColor('#fec980'),
                7: QColor('#f99e59'),
                8: QColor('#e85b3a'),
                9: QColor('#d7191c')
            }
        }

        categories = []

        for cid, unique_value in enumerate(unique_values):
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = QgsSimpleFillSymbolLayer(color=colors[metric][cid],
                                                    strokeColor=QColor('#000000'))

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value) + ' mins' if metric == "time" else " km")
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer('contour', categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setOpacity(0.5)

        layer.triggerRepaint()

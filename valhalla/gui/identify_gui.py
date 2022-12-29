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
from collections import OrderedDict
import shlex
import subprocess
from lxml import etree

from PyQt5.QtCore import QVariant
from qgis.core import (QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsPointXY,
                       QgsGeometry)

from ..utils.convert import decode_polyline6
from ..gui.common_gui import get_locations, get_costing_options


class Identify:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg

        self.path = self.dlg.pbf_file.filePath()

        self.locations = None
        self.costing_options = dict()

    def get_locate_parameters(self):
        """
        Builds parameters across directions functionalities.

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        # API parameters
        profile = self.dlg.routing_travel_combo.currentText()

        params = {
            'costing': profile,
            'verbose': True,
            'id': 1,
        }

        self.locations = get_locations(self.dlg.routing_fromline_list)
        params['locations'] = self.locations

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked():
            params['costing_options'] = dict()
            self.costing_options = params['costing_options'][profile] = get_costing_options(self.dlg.routing_costing_options_group, profile)

        return params

    @staticmethod
    def get_fields(tags):
        """
        Returns fields based on the tags which are present.

        :param tags: Tags in str format, e.g. 'maxspeed=50'
        :type tags: list of str

        :returns: QgsFields
        """

        fields = QgsFields()
        for tag in tags:
            key, value = tag.split('=')
            fields.append(QgsField(key, QVariant.String))

        return fields

    def get_output_feature(self, way):
        """
        Returns the output features with attributes and geometries set.

        :param way: Parsed response for a single way.
        :type way: dict

        :returns: list of QgsFeatures
        :rtype: list of QgsFeature
        """
        feat = QgsFeature()
        qgis_coords = [QgsPointXY(x, y) for y, x in way['geometry']]
        feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))

        values = list()
        for tag in way['tags']:
            value = tag.split('=')[1]
            values.append(value)
        feat.setAttributes(values)

        return feat

    def get_tags(self, response):
        """
        Returns the tags from the list of OSM ID's passed from the locate endpoint.

        :returns: dict of way information, e.g. {<way_id>: {'tags': ['maxspeed=50'], 'shape': 'osagja2p@592'}}
        :rtype: OrderedDict
        """
        cmd = f"osmium getid -o - -f osm --no-progress --default-type=w {self.path}"

        # Parse response from locate and build osmium command
        edges_parsed = OrderedDict()
        for edge_cluster in response:
            for edge in edge_cluster['edges']:
                idx = edge['edge_info']['way_id']
                edges_parsed[idx] = dict()
                edges_parsed[idx]['geometry'] = decode_polyline6(edge['edge_info']['shape'])

                cmd += f' {str(idx)}'

        # Run osmium command
        try:
            output = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            raise e

        # Parse XML from osmium output and include to edges dict
        root_xml = etree.ElementTree(etree.fromstring(output.stdout))
        ways_xml = root_xml.findall('way')
        for way in ways_xml:
            idx = int(way.get('id'))
            tags_xml = way.findall('tag')
            edges_parsed[idx]['tags'] = list()
            for tag in tags_xml:
                edges_parsed[idx]['tags'].append("=".join(tag.values()))

        return edges_parsed
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
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapLayerComboBox
from valhalla.utils import transform

from valhalla.gui.common_gui import get_locations, get_costing_options, get_avoid_polygons


class RoadStats:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg
        self.costing_options = {}

    def get_parameters(self):
        """
        Builds parameters across directions functionalities.

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        # API parameters
        profile = self.dlg.routing_travel_combo.currentText()

        layer: QgsVectorLayer = self.dlg.roads_stats_polygon.currentLayer()
        if layer:
            transformer = transform.transformToWGS(layer.crs())
            feats = layer.getFeatures()
            geoms = [f.geometry() for f in feats]
            locations = list()
            for geom in geoms:
                geom.transform(transformer)
                if geom.wkbType() == QgsWkbTypes.Polygon:
                    # only exterior ring
                    coords = [[[round(pt.x(), 6), round(pt.y(), 6)] for pt in geom.asPolygon()[0]]]
                elif geom.wkbType() == QgsWkbTypes.MultiPolygon:
                    # only exterior ring of each multipolygon sub-polygon
                    coords = [[[round(pt.x(), 6), round(pt.y(), 6)] for pt in poly[0]] for poly in geom.asMultiPolygon()]
                else:
                    raise ValueError(f"WKT type {QgsWkbTypes.displayString(layer.wkbType())} is not supported.")

                locations.extend(coords)
        else:
            locations = [[[loc['lon'], loc['lat']] for loc in get_locations(self.dlg.routing_fromline_list)]]

        params = {'costing': profile, 'stats_props': ["max_grade", "mean_elevation", "max_speed"],
                  'id': 1,
                  'stats_polygons': locations}

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked():
            params['costing_options'] = dict()
            params['costing_options'][profile] = self.costing_options = get_costing_options(self.dlg.routing_costing_options_group, profile)

        # Get Avoids in there
        if self.dlg.avoidlocation_group.isChecked():
            point_locs, poly_locs = get_avoid_polygons(self.dlg.avoidlocation_dropdown.currentLayer(), self.dlg.avoidpolygons_dropdown.currentLayer())
            if point_locs:
                params['exclude_locations'] = point_locs
            if poly_locs:
                params['exclude_polygons'] = poly_locs

        return params

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
from PyQt5.QtWidgets import QSpinBox

from valhalla.gui.common_gui import get_locations, get_costing_options
from valhalla.utils import transform


class Directions:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg

        self.costing_options = dict()

    def get_parameters(self):
        """
        Builds parameters across directions functionalities.

        :returns: All parameter mappings.
        :rtype: dict
        """

        # API parameters
        profile = self.dlg.routing_travel_combo.currentText()
        mode = self.dlg.routing_mode_combo.currentText()
        legal_limit = self.dlg.routing_speed_limit.value()

        params = {
            'costing': profile,
            'narrative': False,
            'id': 1,
        }

        params['locations'] = get_locations(self.dlg.routing_fromline_list)

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked() or mode == 'shortest' or legal_limit:
            params['costing_options'] = dict()
            self.costing_options = params['costing_options'][profile] = get_costing_options(self.dlg.routing_costing_options_group, profile)
            if mode == 'shortest':
                params['costing_options'][profile]['shortest'] = True
            if legal_limit:
                params['costing_options'][profile]['legal_speed'] = legal_limit

        if self.dlg.avoidlocation_group.isChecked():
            point_layer = self.dlg.avoidlocation_dropdown.currentLayer()
            if point_layer:
                locations = list()
                transformer = transform.transformToWGS(point_layer.sourceCrs())
                for feat in point_layer.getFeatures():
                    geom = feat.geometry()
                    geom.transform(transformer)
                    point = geom.asPoint()

                    locations.append({'lon': round(point.x(), 6), 'lat': round(point.y(), 6)})
                params['avoid_locations'] = locations

        return params

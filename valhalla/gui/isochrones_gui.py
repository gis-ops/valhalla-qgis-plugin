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

from ..gui.common_gui import get_costing_options


class Isochrones:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg

        self.costing_options = dict()

    def get_parameters(self, metric):
        """
        Builds parameters across directions functionalities.

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        # API parameters<
        profile = self.dlg.routing_travel_combo.currentText()
        contours = self.dlg.contours.value() if metric == 'time' else self.dlg.contours_distance.value()
        polygons = self.dlg.polygons.currentText()
        denoise = self.dlg.denoise.value()
        generalize = self.dlg.generalize.value()
        mode = self.dlg.routing_mode_combo.currentText()

        contours_obj = list()
        try:
            contours = [float(interval) for interval in contours.split(',')]
            for c in contours:
                contours_obj.append({metric: c})
        except ValueError:
            raise ValueError("Isochrone intervals need to be a comma-separated list of numbers (decimal or whole).")

        polygons = True if polygons == 'Polygon' else False

        params = {
            'costing': profile,
            'show_locations': not self.dlg.iso_no_points.isChecked(),
            'contours': contours_obj,
            'polygons': polygons,
            'id': 1,
        }

        if denoise is not None:
            params['denoise'] = denoise
        if generalize is not None:
            params['generalize'] = generalize

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked() or mode == 'shortest':
            params['costing_options'] = dict()
            self.costing_options = params['costing_options'][profile] = get_costing_options(self.dlg.routing_costing_options_group, profile)
            if mode == 'shortest':
                params['costing_options'][profile]['shortest'] = True

        return params

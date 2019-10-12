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

from valhalla.gui.common_gui import get_costing_options


class Isochrones:
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

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        # API parameters<
        profile = self.dlg.routing_travel_combo.currentText()
        contours = self.dlg.contours.value()
        polygons = self.dlg.polygons.currentText()
        denoise = self.dlg.denoise.value()
        generalize = self.dlg.generalize.value()

        try:
            contours = [{'time': int(interval)} for interval in contours.split(',')]
        except ValueError:
            raise ValueError("Isochrone intervals need to be a comma-separated list of whole numbers.")

        polygons = True if polygons == 'Polygon' else False

        params = {
            'costing': profile,
            'contours': contours,
            'polygons': polygons,
            'id': 1,
        }

        if denoise:
            params['denoise'] = denoise
        if generalize:
            params['generalize'] = generalize

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked():
            params['costing_options'] = dict()
            self.costing_options = params['costing_options'][profile] = get_costing_options(self.dlg.routing_costing_options_group, profile)

        return params

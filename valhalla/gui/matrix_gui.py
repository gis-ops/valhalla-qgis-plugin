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

from ..gui.common_gui import get_locations, get_costing_options


class Matrix:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg

        self.locations = None
        self.costing_options = dict()

    def get_parameters(self):
        """
        Builds parameters across directions functionalities.

        :param bidirectional: If True, will treat all locations as sources and targets.
            If False, will treat the first location as source and all other locations as targets.
        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        # API parameters
        profile = self.dlg.routing_travel_combo.currentText()
        mode = self.dlg.routing_mode_combo.currentText()

        params = {
            'costing': profile,
            'id': 1,
        }

        self.locations = get_locations(self.dlg.routing_fromline_list)
        # figure out directionality for this request
        if self.dlg.matrix_many_to_many.isChecked():
            params['sources'] = self.locations
            params['targets'] = self.locations
        elif self.dlg.matrix_one_to_many.isChecked():
            params['sources'] = self.locations[:1]
            params['targets'] = self.locations[1:]
        else:
            # many to one
            params['sources'] = self.locations[:-1]
            params['targets'] = self.locations[-1:]

        # Get Advanced parameters
        if self.dlg.routing_costing_options_group.isChecked() or mode == 'shortest':
            params['costing_options'] = dict()
            self.costing_options = params['costing_options'][profile] = get_costing_options(self.dlg.routing_costing_options_group, profile)
            if mode == 'shortest':
                params['costing_options'][profile]['shortest'] = True

        return params

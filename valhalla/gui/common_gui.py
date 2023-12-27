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

from qgis.PyQt.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QListWidget


def get_locations(routing_fromline_list: QListWidget, radius: int = 0, heading: int = 0, heading_tol: int = 0):
    """
    Extracts locations from GUI.

    :param routing_fromline_list: The GUI point list.

    :returns: formatted list of locations as Valhalla expects it, i.e. [{"lat": y, "lon": x}, {...}].
    :rtype: list of dict
    """
    locations = []
    for idx in range(routing_fromline_list.count()):
        item = routing_fromline_list.item(idx).text()
        param, coords = item.split(":")
        coords = coords.split(', ')

        loc = {
            'lon': float(coords[0]),
            'lat': float(coords[1]),
        }

        if radius:
            loc['radius'] = radius
        if heading:
            loc['heading'] = heading
        if heading_tol:
            loc['heading_tolerance'] = heading_tol

        locations.append(loc)

    return locations


def get_costing_options(costing_group, profile):
    """
    Extracts checked boxes in costing options parameters.

    :param costing_group: costing group box
    :type avoid_boxes: QgsCollapsibleGroupBox

    :param profile: transportation profile
    :type profile: str

    :returns: parsed costing options
    :rtype: dict
    """

    costing_widgets = costing_group.findChildren((QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox))
    costing_widgets = [o for o in costing_widgets if profile in o.objectName()]

    costing_options = dict()
    for widget in costing_widgets:
        param_name = widget.objectName().replace(profile + '_', '')
        if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            costing_options[param_name] = widget.value()
        if isinstance(widget, QComboBox):
            if widget.currentText():
                costing_options[param_name] = widget.currentText()
        if isinstance(widget, QCheckBox):
            costing_options[param_name] = widget.isChecked()

    return costing_options

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

from PyQt5.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox


def get_locations(routing_fromline_list):
    """
    Extracts locations from GUI.

    :param routing_fromline_list: The GUI point list.
    :type routing_fromline_list: QListWidget

    :returns: formatted list of locations as Valhalla expects it, i.e. [{"lat": y, "lon": x}, {...}].
    :rtype: list of dict
    """
    locations = []
    for idx in range(routing_fromline_list.count()):
        item = routing_fromline_list.item(idx).text()
        param, coords = item.split(":")
        coords = coords.split(', ')

        locations.append({'lon': float(coords[0]), 'lat': float(coords[1])})

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

    costing_widgets = costing_group.findChildren((QComboBox, QSpinBox, QDoubleSpinBox))
    costing_widgets = [o for o in costing_widgets if profile in o.objectName()]

    costing_options = dict()
    for widget in costing_widgets:
        param_name = widget.objectName().replace(profile + '_', '')
        if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            if widget.objectName() == 'truck_length' or widget.objectName() == 'truck_width':
                costing_options[param_name] = round(widget.value() / 3.28084, 2)
            else:
                costing_options[param_name] = widget.value()
        if isinstance(widget, QComboBox):
            if widget.currentText():
                costing_options[param_name] = widget.currentText()
        if isinstance(widget, QCheckBox):
            costing_group[param_name] = widget.isChecked()

    return costing_options

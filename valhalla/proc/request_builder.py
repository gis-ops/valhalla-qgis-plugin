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
import inspect

from qgis.core import QgsPointXY, QgsWkbTypes

from valhalla.utils import transform
from valhalla.common import TRUCK_COSTING
from .costing_params import CostingAuto

def get_directions_params(points, profile, costing_options, mode):
    """
    Get the full list of parameters except for avoiding points.

    :param points: Point list
    :type points: list of QgsPointXY

    :param profile: transportation profile
    :type profile: str

    :param costing_options: costing options class with costing options as attributes
    :type costing_options: CostingAuto

    :param mode: fastest or shortest
    :type mode: str

    :returns: dict of Vahalla directions parameters
    :rtype: dict
    """
    params = dict(
        costing=profile,
        show_locations=True
    )
    params['locations'] = get_locations(points)

    costing_params = get_costing_options(costing_options, profile, mode)

    if costing_params:
        params['costing_options'] = costing_params

    return params

def get_locations(points):
    """
    Get the locations parameter value.

    :param points: List of QgsPointXY
    :type points: list of QgsPointXY

    :returns: Valhalla locations list
    :rtype: list of dict
    """

    return [{"lon": round(point.x(), 6), "lat": round(point.y(), 6)} for point in points]


def get_costing_options(costing_options, profile, mode):
    """
    Get the costing_options parameter value per profile.

    :param costing_options: costing options class with costing options as attributes
    :type costing_options: CostingAuto

    :param profile: transportation profile
    :type profile: str

    :param mode: fastest or shortest
    :type mode: str

    :returns: profile specific costing options
    :rtype: dict of dict
    """
    params = dict()

    costing_options = inspect.getmembers(costing_options, lambda a:not(inspect.isroutine(a)))
    costing_options = [a for a in costing_options if not(a[0].startswith('__') and a[0].endswith('__'))]

    if any([cost[1] for cost in costing_options]) or mode == 'Shortest':
        params[profile] = dict()
        for cost in costing_options:
            if cost[1]:
                if cost[0] in [TRUCK_COSTING.WIDTH, TRUCK_COSTING.LENGTH]:  # Temp bcs of Valhalla issue
                    params[profile][cost[0]] = round(cost[1] / 3.28084, 2)
                else:
                    params[profile][cost[0]] = cost[1]
        if mode == 'Shortest':
            params[profile]['shortest'] = True

    return params


def get_avoid_locations(avoid_layer):
    """
    Get the avoid locations parameter value.

    :param avoid_layer: The point layer to be avoided
    :type avoid_layer: QgsProcessingFeatureSource

    :returns: Valhalla formatted locations list
    :rtype: list of dict
    """

    locations = []
    xformer_avoid = transform.transformToWGS(avoid_layer.sourceCrs())
    if avoid_layer.wkbType() != QgsWkbTypes.MultiPoint:
        points = []
        for feat in avoid_layer.getFeatures():
            points.append(xformer_avoid.transform(QgsPointXY(feat.geometry().asPoint())))

        for point in points:
            locations.append({"lon": round(point.x(), 6), "lat": round(point.y(), 6)})

    return locations

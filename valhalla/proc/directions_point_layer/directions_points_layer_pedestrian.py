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
from .directions_points_layer_auto import ValhallaRoutePointsLayerCarAlgo
from ..costing_params import CostingPedestrian

class ValhallaRoutePointsLayerPedestrianAlgo(ValhallaRoutePointsLayerCarAlgo):

    ALGO_NAME = 'directions_from_point_layer_pedestrian'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    COSTING = CostingPedestrian
    PROFILE = 'pedestrian'

    def createInstance(self):
        return ValhallaRoutePointsLayerPedestrianAlgo()

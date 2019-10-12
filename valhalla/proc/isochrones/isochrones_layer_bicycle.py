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
from ..costing_params import CostingBicycle
from .isochrones_layer_auto import ValhallaIsochronesCarAlgo


class ValhallaIsochronesBicycleAlgo(ValhallaIsochronesCarAlgo):

    ALGO_NAME = 'isochrones_bicycle'

    COSTING = CostingBicycle
    PROFILE = 'bicycle'

    def createInstance(self):
        return ValhallaIsochronesBicycleAlgo()

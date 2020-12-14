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

PROFILES = [
    'auto',
    'truck',
    'bicycle',
    'pedestrian'
]

BICYCLE_TYPES = [
    'Hybrid',
    'Road',
    'Cross',
    'Mountain'
]


class AUTO_COSTING:
    PENALTY_MANEUVER = "maneuver_penalty"
    PENALTY_BORDERS = "country_crossing_penalty"
    PENALTY_TOLL_BOOTH = "toll_booth_penalty"
    COST_GATES = "gate_cost"
    COST_FERRY = "ferry_cost"
    COST_BORDERS = "country_crossing_cost"
    COST_TOLL_BOOTH = "toll_booth_cost"
    USE_HIGHWAYS = "use_highways"
    USE_FERRY = "use_ferry"
    USE_TOLLS = "use_tolls"


class TRUCK_COSTING:
    WEIGHT = 'weight'
    HEIGHT = 'height'
    WIDTH = 'width'
    LENGTH = 'length'
    AXLE_LOAD = 'axle_load'
    HAZMAT = 'hazmat'


class BICYCLE_COSTING:
    TYPE = 'bicycle_type'
    SPEED = 'cycling_speed'
    PENALTY_MANEUVER = "maneuver_penalty"
    PENALTY_BORDERS = "country_crossing_penalty"
    COST_BORDERS = "country_crossing_cost"
    COST_GATES = "gate_cost"
    USE_FERRY = "use_ferry"
    USE_ROADS = 'use_roads'
    USE_HILLS = 'use_hills'
    AVOID_SURFACE = 'avoid_bad_surfaces'

class PED_COSTING:
    SPEED = 'weight'
    MAX_DIFF = 'max_hiking_difficulty'
    PENALTY_STEPS = 'step_penalty'
    USE_FERRY = 'use_ferry'
    FACTOR_WALKWAY = 'walkway_factor'
    FACTOR_ALLEY = 'alley_factor'
    FACTOR_DRIVEWAY = 'driveway_factor'

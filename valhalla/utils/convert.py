# -*- coding: utf-8 -*-
"""
/***************************************************************************
 valhalla
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
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


def _trans(value, index):
    """
    Copyright (c) 2014 Bruno M. Custódio
    Copyright (c) 2016 Frederick Jansen
    https://github.com/hicsail/polyline/commit/ddd12e85c53d394404952754e39c91f63a808656
    """
    byte, result, shift = None, 0, 0

    while byte is None or byte >= 0x20:
        byte = ord(value[index]) - 63
        index += 1
        result |= (byte & 0x1f) << shift
        shift += 5
        comp = result & 1

    return ~(result >> 1) if comp else (result >> 1), index


def decode_polyline6(expression, precision=6, is3d=False):
    """
    Copyright (c) 2014 Bruno M. Custódio
    Copyright (c) 2016 Frederick Jansen
    https://github.com/hicsail/polyline/commit/ddd12e85c53d394404952754e39c91f63a808656
    """
    coordinates, index, lat, lng, z, length, factor = [], 0, 0, 0, 0, len(
        expression), float(10 ** precision)

    while index < length:
        lat_change, index = _trans(expression, index)
        lng_change, index = _trans(expression, index)
        lat += lat_change
        lng += lng_change
        if not is3d:
            coordinates.append((lat / factor, lng / factor))
        else:
            z_change, index = _trans(expression, index)
            z += z_change
            coordinates.append((lat / factor, lng / factor, z / 100))

    return coordinates

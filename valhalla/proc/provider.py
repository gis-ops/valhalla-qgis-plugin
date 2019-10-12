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

from PyQt5.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from valhalla import RESOURCE_PREFIX, PLUGIN_NAME, __version__
from .directions_lines.directions_lines_auto import ValhallaRouteLinesCarAlgo
from .directions_lines.directions_lines_truck import ValhallaRouteLinesTruckAlgo
from .directions_lines.directions_lines_bicycle import ValhallaRouteLinesBicycleAlgo
from .directions_lines.directions_lines_pedestrian import ValhallaRouteLinesPedestrianAlgo
from .directions_point_layer.directions_points_layer_auto import ValhallaRoutePointsLayerCarAlgo
from .directions_point_layer.directions_points_layer_truck import ValhallaRoutePointsLayerTruckAlgo
from .directions_point_layer.directions_points_layer_bicycle import ValhallaRoutePointsLayerBicycleAlgo
from .directions_point_layer.directions_points_layer_pedestrian import ValhallaRoutePointsLayerPedestrianAlgo
from .directions_points_layers.directions_points_layers_auto import ValhallaRoutePointsLayersCarAlgo
from .directions_points_layers.directions_points_layers_truck import ValhallaRoutePointsLayersTruckAlgo
from .directions_points_layers.directions_points_layers_bicycle import ValhallaRoutePointsLayersBicycleAlgo
from .directions_points_layers.directions_points_layers_pedestrian import ValhallaRoutePointsLayersPedestrianAlgo
from .isochrones.isochrones_layer_auto import ValhallaIsochronesCarAlgo
from .isochrones.isochrones_layer_truck import ValhallaIsochronesTruckAlgo
from .isochrones.isochrones_layer_bicycle import ValhallaIsochronesBicycleAlgo
from .isochrones.isochrones_layer_pedestrian import ValhallaIsochronesPedestrianAlgo
from .matrix.matrix_auto import ValhallaMatrixCarAlgo
from .matrix.matrix_truck import ValhallaMatrixTruckAlgo
from .matrix.matrix_bicycle import ValhallaMatrixBicycleAlgo
from .matrix.matrix_pedestrian import ValhallaMatrixPedestrianAlgo


class ValhallaProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

        # Load algorithms
        self.alglist = [
            ValhallaRouteLinesCarAlgo(),
            ValhallaRouteLinesTruckAlgo(),
            ValhallaRouteLinesBicycleAlgo(),
            ValhallaRouteLinesPedestrianAlgo(),
            ValhallaRoutePointsLayerCarAlgo(),
            ValhallaRoutePointsLayerBicycleAlgo(),
            ValhallaRoutePointsLayerPedestrianAlgo(),
            ValhallaRoutePointsLayerTruckAlgo(),
            ValhallaRoutePointsLayersCarAlgo(),
            ValhallaRoutePointsLayersTruckAlgo(),
            ValhallaRoutePointsLayersBicycleAlgo(),
            ValhallaRoutePointsLayersPedestrianAlgo(),
            ValhallaIsochronesCarAlgo(),
            ValhallaIsochronesTruckAlgo(),
            ValhallaIsochronesBicycleAlgo(),
            ValhallaIsochronesPedestrianAlgo(),
            ValhallaMatrixCarAlgo(),
            ValhallaMatrixTruckAlgo(),
            ValhallaMatrixBicycleAlgo(),
            ValhallaMatrixPedestrianAlgo(),
        ]

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        for alg in self.alglist:
            self.addAlgorithm(alg)

    def icon(self):
        return QIcon(RESOURCE_PREFIX + 'icon_valhalla.png')

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return PLUGIN_NAME.strip()

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return PLUGIN_NAME

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return PLUGIN_NAME + ' plugin v' + __version__

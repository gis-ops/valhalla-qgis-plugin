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

import os.path

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDefinition,
                       )
from .. import HELP_DIR
from ... import RESOURCE_PREFIX, __help__
from ...common import client, directions_core
from ...utils import configmanager, transform, exceptions,logger
from ..costing_params import CostingAuto
from ..request_builder import get_directions_params, get_avoid_locations


class ValhallaRoutePointsLayersCarAlgo(QgsProcessingAlgorithm):

    ALGO_NAME = 'directions_from_points_2_layers_auto'
    ALGO_NAME_LIST = ALGO_NAME.split('_')
    MODE_SELECTION = ['Row-by-Row', 'All-by-All']

    HELP = 'algorithm_directions_points.help'

    COSTING = CostingAuto
    PROFILE = 'auto'
    MODE_TYPES = ['Fastest', 'Shortest']

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_START = "INPUT_START_LAYER"
    IN_START_FIELD = "INPUT_START_FIELD"
    IN_END = "INPUT_END_LAYER"
    IN_END_FIELD = "INPUT_END_FIELD"
    IN_MATRIX_MODE = "INPUT_MATRIX_MODE"
    IN_MODE = "INPUT_MODE"
    IN_AVOID = "avoid_locations"
    OUT = 'OUTPUT'

    def __init__(self):
        super(ValhallaRoutePointsLayersCarAlgo, self).__init__()
        self.providers = configmanager.read_config()['providers']
        self.costing_options = self.COSTING()

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        providers = [provider['name'] for provider in self.providers]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROVIDER,
                "Provider",
                providers,
                defaultValue=providers[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_START,
                description="Input Start Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_START_FIELD,
                description="Start ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_START,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_END,
                description="Input End Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_END_FIELD,
                description="End ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_END,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_MATRIX_MODE,
                "Layer mode",
                self.MODE_SELECTION,
                defaultValue=self.MODE_SELECTION[0]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_MODE,
                'Mode',
                options=self.MODE_TYPES,
                defaultValue=self.MODE_TYPES[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_AVOID,
                description="Point layer with locations to avoid",
                types=[QgsProcessing.TypeVectorPoint],
                optional=True
            )
        )

        advanced = self.costing_options.get_costing_params()

        for p in advanced:
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            self.addParameter(p)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Routing " + self.PROFILE.capitalize() + " From 2 Points",
                createByDefault=False
            )
        )

    def group(self):
        return self.PROFILE.capitalize()

    def groupId(self):
        return self.PROFILE

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            self.HELP
        )
        with open(file) as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return " ".join(map(lambda x: x.capitalize(), self.ALGO_NAME_LIST))

    def icon(self):
        return QIcon(RESOURCE_PREFIX + 'icon_directions.png')

    def createInstance(self):
        return ValhallaRoutePointsLayersCarAlgo()

    def processAlgorithm(self, parameters, context, feedback):

        # Init ORS client

        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        mode = self.MODE_TYPES[self.parameterAsEnum(parameters, self.IN_MODE, context)]

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_START,
            context
        )
        source_field_name = self.parameterAsString(
            parameters,
            self.IN_START_FIELD,
            context
        )
        destination = self.parameterAsSource(
            parameters,
            self.IN_END,
            context
        )
        destination_field_name = self.parameterAsString(
            parameters,
            self.IN_END_FIELD,
            context
        )

        matrix_mode = self.MODE_SELECTION[self.parameterAsEnum(
            parameters,
            self.IN_MATRIX_MODE,
            context
        )]

        avoid_layer = self.parameterAsLayer(
            parameters,
            self.IN_AVOID,
            context
        )

        # Get fields from field name
        source_field_id = source.fields().lookupField(source_field_name)
        source_field = source.fields().field(source_field_id)
        destination_field_id = destination.fields().lookupField(destination_field_name)
        destination_field = destination.fields().field(destination_field_id)

        route_dict = self._get_route_dict(
            source,
            source_field,
            destination,
            destination_field
        )

        if matrix_mode == 'Row-by-Row':
            route_count = min([source.featureCount(), destination.featureCount()])
        else:
            route_count = source.featureCount() * destination.featureCount()

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(source_field.type(), destination_field.type()),
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem(4326))

        counter = 0

        params = dict()
        if avoid_layer:
            params['avoid_locations'] = get_avoid_locations(avoid_layer)

        # Sets all advanced parameters as attributes of self.costing_options
        self.costing_options.set_costing_options(self, parameters, context)

        for points, values in directions_core.get_request_point_features(route_dict, matrix_mode):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params.update(get_directions_params(points, self.PROFILE, self.costing_options, mode))
            params['id'] = f"{values[0]} & {values[1]}"

            try:
                response = clnt.request('/route', post_json=params)
            except (exceptions.ApiError) as e:
                msg = "Route from {} to {} caused a {}:\n{}".format(
                    values[0],
                    values[1],
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg)
                continue

            except (exceptions.InvalidKey, exceptions.GenericServerError) as e:
                msg = "{}:\n{}".format(
                    e.__class__.__name__,
                    str(e))
                logger.log(msg)
                raise

            options = {}
            if params.get('costing_options'):
                options = params['costing_options']

            sink.addFeature(directions_core.get_output_feature_directions(
                response,
                self.PROFILE,
                options.get(self.PROFILE),
                from_value=values[0],
                to_value=values[1]
            ))

            counter += 1
            feedback.setProgress(int(100.0 / route_count * counter))

        return {self.OUT: dest_id}

    def _get_route_dict(self, source, source_field, destination, destination_field):
        """
        Compute route_dict from input layer.

        :param source: Input from layer
        :type source: QgsProcessingParameterFeatureSource

        :param source_field: ID field from layer.
        :type source_field: QgsField

        :param destination: Input to layer.
        :type destination: QgsProcessingParameterFeatureSource

        :param destination_field: ID field to layer.
        :type destination_field: QgsField

        :returns: route_dict with coordinates and ID values
        :rtype: dict
        """
        route_dict = dict()

        source_feats = list(source.getFeatures())
        xformer_source = transform.transformToWGS(source.sourceCrs())
        route_dict['start'] = dict(
            geometries=[xformer_source.transform(feat.geometry().asPoint()) for feat in source_feats],
            values= [feat.attribute(source_field.name()) for feat in source_feats],
        )

        destination_feats = list(destination.getFeatures())
        xformer_destination = transform.transformToWGS(destination.sourceCrs())
        route_dict['end'] = dict(
            geometries=[xformer_destination.transform(feat.geometry().asPoint()) for feat in destination_feats],
            values= [feat.attribute(destination_field.name()) for feat in destination_feats],
        )

        return route_dict

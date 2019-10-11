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
                       QgsProcessingParameterMapLayer,
                       QgsPointXY,
                       )
from .. import HELP_DIR
from valhalla import RESOURCE_PREFIX, __help__
from valhalla.common import client, directions_core
from valhalla.utils import configmanager, transform, exceptions,logger
from ..costing_params import CostingAuto
from ..request_builder import get_directions_params, get_avoid_locations

class ValhallaRoutePointsLayerCarAlgo(QgsProcessingAlgorithm):

    ALGO_NAME = 'directions_from_point_layer_auto'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    HELP = 'algorithm_directions_point.help'

    COSTING = CostingAuto
    PROFILE = 'auto'

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINT = "INPUT_LINE_LAYER"
    IN_FIELD = "INPUT_LAYER_FIELD"
    IN_AVOID = "avoid_locations"
    OUT = 'OUTPUT'

    def __init__(self):
        super(ValhallaRoutePointsLayerCarAlgo, self).__init__()
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
                name=self.IN_POINT,
                description="Input Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Layer ID Field",
                parentLayerParameterName=self.IN_POINT,
            )
        )

        self.addParameter(
            QgsProcessingParameterMapLayer(
                name=self.IN_AVOID,
                description="Point layer with locations to avoid",
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
                description="Valhalla_Routing_Point_" + self.PROFILE,
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
        return ValhallaRoutePointsLayerCarAlgo()

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client

        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_POINT,
            context
        )

        source_field_name = self.parameterAsString(
            parameters,
            self.IN_FIELD,
            context
        )

        avoid_layer = self.parameterAsLayer(
            parameters,
            self.IN_AVOID,
            context
        )

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(from_type=source.fields().field(source_field_name).type(),
                                                                          from_name=source_field_name,
                                                                          line=True),
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem(4326))
        input_points = list()
        from_values = list()
        xformer_source = transform.transformToWGS(source.sourceCrs())

        if source.wkbType() == QgsWkbTypes.Point:
            points = list()
            for feat in sorted(source.getFeatures(), key=lambda f: f.id()):
                points.append(xformer_source.transform(QgsPointXY(feat.geometry().asPoint())))
            input_points.append(points)
            from_values.append('')
        elif source.wkbType() == QgsWkbTypes.MultiPoint:
            # loop through multipoint features
            for feat in sorted(source.getFeatures(), key=lambda f: f.id()):
                points = list()
                for point in feat.geometry().asMultiPoint():
                    points.append(xformer_source.transform(QgsPointXY(point)))
                input_points.append(points)
                from_values.append(feat[source_field_name])

        # Init ORS client
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        count = source.featureCount()

        params = dict()
        if avoid_layer:
            params['avoid_locations'] = get_avoid_locations(avoid_layer)

        for num, (points, from_value) in enumerate(zip(input_points, from_values)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params.update(get_directions_params(points, self.PROFILE, self.costing_options))
            params['id'] = from_value

            try:
                response = clnt.request('/route', post_json=params)
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = "Feature ID {} caused a {}:\n{}".format(
                    from_value,
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg)
                continue

            options = {}
            if params.get('costing_options'):
                options = params['costing_options']

            sink.addFeature(directions_core.get_output_feature_directions(
                response,
                self.PROFILE,
                options.get(self.PROFILE),
                from_value=from_value
            ))

            feedback.setProgress(int(100.0 / count * num))

        return {self.OUT: dest_id}

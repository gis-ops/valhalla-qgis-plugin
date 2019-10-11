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
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       )
from .. import HELP_DIR
from valhalla import RESOURCE_PREFIX, __help__
from valhalla.common import client, directions_core, PROFILES
from valhalla.utils import configmanager, transform, exceptions,logger, convert
from ..costing_params import CostingAuto
from ..request_builder import get_directions_params


class ValhallaRouteLinesCarAlgo(QgsProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    ALGO_NAME = 'directions_from_polylines_auto'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    HELP = 'algorithm_directions_line.help'

    COSTING = CostingAuto
    PROFILE = 'auto'

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_LINES = "INPUT_LINE_LAYER"
    IN_FIELD = "INPUT_LAYER_FIELD"
    OUT = 'OUTPUT'

    def __init__(self):
        super(ValhallaRouteLinesCarAlgo, self).__init__()
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
                name=self.IN_LINES,
                description="Input Line layer",
                types=[QgsProcessing.TypeVectorLine],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Layer ID Field",
                parentLayerParameterName=self.IN_LINES,
            )
        )

        advanced = self.costing_options.get_costing_params()

        for p in advanced:
            p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            self.addParameter(p)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Valhalla_Routing_Lines_" + self.PROFILE,
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
        return ValhallaRouteLinesCarAlgo()

    def processAlgorithm(self, parameters, context, feedback):

        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_LINES,
            context
        )

        source_field_name = self.parameterAsString(
            parameters,
            self.IN_FIELD,
            context
        )

        # Sets all advanced parameters as attributes of self.costing_options
        self.costing_options.set_costing_options(self, parameters, context)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(from_type=source.fields().field(source_field_name).type(),
                                                                          from_name=source_field_name,
                                                                          line=True),
                                               source.wkbType(),
                                               QgsCoordinateReferenceSystem(4326))

        self._make_request(source, sink, provider, source_field_name, feedback)

        return {self.OUT: dest_id}

    @staticmethod
    def _get_sorted_lines(layer, field_name):
        """
        Generator to yield geometry and ID value sorted by feature ID. Careful: feat.id() is not necessarily
        permanent

        :param layer: source input layer
        :type layer: QgsProcessingParameterFeatureSource

        :param field_name: name of ID field
        :type field_name: str
        """
        # First get coordinate transformer
        xformer = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            line = None
            field_value = feat[field_name]
            # for
            if layer.wkbType() == QgsWkbTypes.MultiLineString:
                # TODO: only takes the first polyline geometry from the multiline geometry currently
                # Loop over all polyline geometries
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asMultiPolyline()[0]]

            elif layer.wkbType() == QgsWkbTypes.LineString:
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asPolyline()]

            yield line, field_value

    def _make_request(self, source, sink, provider, source_field_name, feedback, extra_params={}):

        # Init ORS client
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        count = source.featureCount()

        for num, (line, field_value) in enumerate(self._get_sorted_lines(source, source_field_name)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                params = get_directions_params(line, self.PROFILE, self.costing_options)
                params['id'] = field_value
                params.update(extra_params)
                response = clnt.request('/route', post_json=params)
                options = {}
                if params.get('costing_options'):
                    options = params['costing_options']

                sink.addFeature(directions_core.get_output_feature_directions(
                    response,
                    self.PROFILE,
                    options.get(self.PROFILE),
                    from_value=field_value
                ))
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = "Feature ID {} caused a {}:\n{}".format(
                    field_value,
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg)
                continue

            feedback.setProgress(int(100.0 / count * num))

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
                       QgsProcessingException,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterMapLayer,
                       )
from .. import HELP_DIR
from ... import RESOURCE_PREFIX, __help__
from ...common import client, matrix_core
from ...utils import configmanager, transform, exceptions, logger
from ..costing_params import CostingAuto
from ..request_builder import get_locations, get_costing_options, get_avoid_locations


class ValhallaMatrixCarAlgo(QgsProcessingAlgorithm):

    ALGO_NAME = 'matrix_auto'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    HELP = 'algorithm_directions_points.help'

    COSTING = CostingAuto
    PROFILE = 'auto'
    MODE_TYPES = ['Fastest', 'Shortest']

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_START = "INPUT_START_LAYER"
    IN_START_FIELD = "INPUT_START_FIELD"
    IN_END = "INPUT_END_LAYER"
    IN_END_FIELD = "INPUT_END_FIELD"
    IN_MODE = "INPUT_MODE"
    IN_AVOID = "avoid_locations"
    OUT = 'OUTPUT'

    def __init__(self):
        super(ValhallaMatrixCarAlgo, self).__init__()
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
                description="Matrix " + self.PROFILE.capitalize(),
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
        return QIcon(RESOURCE_PREFIX + 'icon_matrix.png')

    def createInstance(self):
        return ValhallaMatrixCarAlgo()

    def processAlgorithm(self, parameters, context, feedback):

        # Init ORS client
        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda: feedback.reportError("OverQueryLimit: Retrying"))

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
        avoid_layer = self.parameterAsSource(
            parameters,
            self.IN_AVOID,
            context
        )

        # Get fields from field name
        source_field_id = source.fields().lookupField(source_field_name)
        source_field = source.fields().field(source_field_id)

        destination_field_id = destination.fields().lookupField(destination_field_name)
        destination_field = destination.fields().field(destination_field_id)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            matrix_core.get_fields(
                source_field.type(),
                destination_field.type()
            ),
            QgsWkbTypes.NoGeometry
        )

        # Abort when MultiPoint type
        if (source.wkbType() or destination.wkbType()) == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get feature amounts/counts
        sources_amount = source.featureCount()
        destinations_amount = destination.featureCount()
        if (sources_amount or destinations_amount) > 10000:
            raise QgsProcessingException(
                "ProcessingError: Too large input, please decimate."
            )

        sources_features = list(source.getFeatures())
        destinations_features = list(destination.getFeatures())

        # Get source and destination features
        xformer_source = transform.transformToWGS(source.sourceCrs())
        sources_points = [xformer_source.transform(feat.geometry().asPoint()) for feat in sources_features]
        xformer_destination = transform.transformToWGS(destination.sourceCrs())
        destination_points = [xformer_destination.transform(feat.geometry().asPoint()) for feat in destinations_features]

        # Build params
        params = dict(
            costing=self.PROFILE
        )

        # Sets all advanced parameters as attributes of self.costing_options
        self.costing_options.set_costing_options(self, parameters, context)

        costing_params = get_costing_options(self.costing_options, self.PROFILE, mode)
        if costing_params:
            params['costing_options'] = costing_params

        if avoid_layer:
            params['avoid_locations'] = get_avoid_locations(avoid_layer)

        sources_attributes = [feat.attribute(source_field_name) for feat in sources_features]
        destinations_attributes = [feat.attribute(destination_field_name) for feat in destinations_features]

        source_attr_iter = self._chunks(sources_attributes, 50)
        for sources in self._chunks(sources_points, 50):
            params["sources"] = get_locations(sources)
            source_attributes = next(source_attr_iter)

            destination_attr_iter = self._chunks(destinations_attributes, 50)
            for destinations in self._chunks(destination_points, 50):
                params["targets"] = get_locations(destinations)
                params["id"] = "matrix"
                destination_attributes = next(destination_attr_iter)

                # Make request and catch ApiError
                try:
                    response = clnt.request('/sources_to_targets', post_json=params)
                except (exceptions.ApiError) as e:
                    msg = "{}: {}".format(
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

                feats = matrix_core.get_output_features_matrix(
                    response,
                    self.PROFILE,
                    costing_params,
                    False,
                    source_attributes,
                    destination_attributes
                )

                for feat in feats:
                    sink.addFeature(feat)

        return {self.OUT: dest_id}

    @staticmethod
    def _chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

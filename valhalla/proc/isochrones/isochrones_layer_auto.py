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
from copy import deepcopy

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingException,
                       QgsProcessingParameterMapLayer,
                       )
from .. import HELP_DIR
from valhalla import RESOURCE_PREFIX, __help__
from valhalla.common import client, isochrones_core
from valhalla.utils import configmanager, transform, exceptions,logger
from ..costing_params import CostingAuto
from ..request_builder import get_directions_params, get_avoid_locations


class ValhallaIsochronesCarAlgo(QgsProcessingAlgorithm):

    ALGO_NAME = 'isochrones_auto'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    HELP = 'algorithm_isochrone_layer.help'

    COSTING = CostingAuto
    PROFILE = 'auto'

    GEOMETRY_TYPES = ['LineString', 'Polygon']

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINTS = "INPUT_POINT_LAYER"
    IN_FIELD = "INPUT_FIELD"
    IN_INTERVALS = 'contours'
    IN_DENOISE = 'denoise'
    IN_GENERALIZE = 'generalize'
    IN_GEOMETRY = 'polygons'
    IN_AVOID = "avoid_locations"
    OUT = 'OUTPUT'

    # Save some important references
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem(4326)

    def __init__(self):
        super(ValhallaIsochronesCarAlgo, self).__init__()
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
                name=self.IN_POINTS,
                description="Input Point layer",
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Input layer ID Field",
                parentLayerParameterName=self.IN_POINTS
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_INTERVALS,
                description="Comma-separated ranges [mins]",
                defaultValue="5, 10"
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_DENOISE,
                description="Denoise parameter (0.0-1.0)",
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_GENERALIZE,
                description="Generalize parameter for Douglas-Peucker",
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.IN_GEOMETRY,
                options=self.GEOMETRY_TYPES,
                description="Output geometry type",
                optional=True
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
                description="Valhalla_Isochrones_" + self.PROFILE,
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
        return QIcon(RESOURCE_PREFIX + 'icon_isochrones.png')

    def createInstance(self):
        return ValhallaIsochronesCarAlgo()

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client
        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        params = dict()

        denoise = self.parameterAsDouble(parameters, self.IN_DENOISE, context)
        if denoise:
            params[self.IN_DENOISE] = denoise

        generalize = self.parameterAsDouble(parameters, self.IN_GENERALIZE, context)
        if generalize:
            params[self.IN_GENERALIZE] = generalize

        intervals_raw = self.parameterAsString(parameters, self.IN_INTERVALS, context)
        params['contours'] = [{"time": int(x)} for x in intervals_raw.split(',')]

        source = self.parameterAsSource(parameters, self.IN_POINTS, context)
        if source.wkbType() == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        avoid_layer = self.parameterAsLayer(
            parameters,
            self.IN_AVOID,
            context
        )
        avoid_param = get_avoid_locations(avoid_layer)
        if avoid_param:
            params['avoid_locations'] = avoid_param

        # Get ID field properties
        id_field_name = self.parameterAsString(parameters, self.IN_FIELD, context)
        id_field_id = source.fields().lookupField(id_field_name)
        if id_field_name == '':
            id_field_id = 0
            id_field_name = source.fields().field(id_field_id).name()
        id_field = source.fields().field(id_field_id)

        geometry_param = self.GEOMETRY_TYPES[self.parameterAsEnum(parameters, self.IN_GEOMETRY, context)]
        geometry_type = QgsWkbTypes.Polygon if geometry_param == 'Polygon' else QgsWkbTypes.LineString
        params[self.IN_GEOMETRY] = True if geometry_param == 'Polygon' else False

        # Populate iso_layer instance with parameters
        self.isochrones.set_parameters(self.PROFILE, geometry_param, id_field.type(), id_field_name)

        # Sets all advanced parameters as attributes of self.costing_options
        self.costing_options.set_costing_options(self, parameters, context)

        # Make the actual requests
        requests = []
        for properties in self.get_sorted_feature_parameters(source):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Get transformed coordinates and feature
            locations, feat = properties
            params.update(get_directions_params(locations, self.PROFILE, self.costing_options))
            params['id'] = feat[id_field_name]
            requests.append(deepcopy(params))

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    geometry_type,
                                                    self.crs_out)

        for num, params in enumerate(requests):
            if feedback.isCanceled():
                break

            # If feature causes error, report and continue with next
            try:
                # Populate features from response
                response = clnt.request('/isochrone', post_json=params)

            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = "Feature ID {} caused a {}:\n{}".format(
                    params['id'],
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg, 2)
                continue

            options = {}
            if params.get('costing_options'):
                options = params['costing_options']

            for isochrone in self.isochrones.get_features(response, params['id'], options.get(self.PROFILE)):
                sink.addFeature(isochrone)

            feedback.setProgress(int(100.0 / source.featureCount() * num))

        return {self.OUT: self.dest_id}

    def postProcessAlgorithm(self, context, feedback):
        """Style polygon layer in post-processing step."""
        # processed_layer = self.isochrones.calculate_difference(self.dest_id, context)
        processed_layer= QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}

    def get_sorted_feature_parameters(self, layer):
        """
        Generator to yield geometry and id of features sorted by feature ID. Careful: feat.id() is not necessarily
        permanent

        :param layer: source input layer.
        :type layer: QgsProcessingParameterFeatureSource
        """
        # First get coordinate transformer
        xformer = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            x_point = xformer.transform(feat.geometry().asPoint())

            yield ([x_point], feat)


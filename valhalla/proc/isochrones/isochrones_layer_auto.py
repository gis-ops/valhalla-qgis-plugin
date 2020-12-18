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
from copy import deepcopy

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsVectorLayer,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingException,
                       QgsProcessingOutputVectorLayer,
QgsProcessingContext
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

    GEOMETRY_TYPES = ['Polygon', 'LineString']

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINTS = "INPUT_POINT_LAYER"
    IN_FIELD = "INPUT_FIELD"
    IN_INTERVALS_TIME = 'contours'
    IN_INTERVALS_DISTANCE = 'contours_distance'
    IN_SHOW_LOCATIONS = 'show_locations'
    IN_DENOISE = 'denoise'
    IN_GENERALIZE = 'generalize'
    IN_GEOMETRY = 'polygons'
    IN_AVOID = "avoid_locations"
    OUT_TIME = 'OUTPUT_TIME'
    OUT_DISTANCE = 'OUTPUT_DISTANCE'
    POINTS_SNAPPED = 'OUTPUT_SNAPPED_POINTS'
    POINTS_INPUT = 'OUTPUT_INPUT_POINTS'

    # Save some important references
    isos_time_id = None
    isos_dist_id = None
    points_snapped_id = None
    points_input_id = None
    isochrones = isochrones_core.Isochrones()
    crs_out = QgsCoordinateReferenceSystem('ESPG:4326')

    def __init__(self):
        super(ValhallaIsochronesCarAlgo, self).__init__()
        self.providers = configmanager.read_config()['providers']
        self.costing_options = self.COSTING()
        self.intervals = None  # will be populated with the intervals available
        self.isos_time_id, self.isos_dist_id, self.points_input_id, self.points_snapped_id= None, None, None, None


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
                name=self.IN_INTERVALS_TIME,
                description="Comma-separated time intervals [mins]",
                defaultValue="5,10",
                optional=True
            )
        )

        #self.addParameter(
        #    QgsProcessingParameterString(
        #        name=self.IN_INTERVALS_DISTANCE,
         #       description="Comma-separated distance intervals [km]",
        #        defaultValue="5,10",
        #        optional=True
        #    )
        #)

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.IN_SHOW_LOCATIONS,
                description="Return input locations as (Multi)Point",
                defaultValue=False
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
                defaultValue=self.GEOMETRY_TYPES[0],
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

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUT_TIME,
                description="Isochrones " + self.PROFILE,
                type=QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.OUT_DISTANCE,
                description="Isodistances " + self.PROFILE,
                type=QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.POINTS_SNAPPED,
                description="",
                type=QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addOutput(
            QgsProcessingOutputVectorLayer(
                name=self.POINTS_INPUT,
                description="",
                type=QgsProcessing.TypeVectorAnyGeometry
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

        geometry_param = self.GEOMETRY_TYPES[self.parameterAsEnum(parameters, self.IN_GEOMETRY, context)]
        geometry_type = QgsWkbTypes.Polygon if geometry_param == 'Polygon' else QgsWkbTypes.LineString
        params[self.IN_GEOMETRY] = True if geometry_param == 'Polygon' else False

        source = self.parameterAsSource(parameters, self.IN_POINTS, context)
        if source.wkbType() == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get ID field properties
        id_field_name = self.parameterAsString(parameters, self.IN_FIELD, context)
        id_field_id = source.fields().lookupField(id_field_name)
        if id_field_name == '':
            id_field_id = 0
            id_field_name = source.fields().field(id_field_id).name()
        id_field = source.fields().field(id_field_id)

        # Populate iso_layer instance with parameters
        self.isochrones.set_parameters(self.PROFILE, geometry_param, id_field.type(), id_field_name)

        layer_time = QgsVectorLayer(
            f'{geometry_param}?crs=EPSG:4326',
            f'Isochrones {self.PROFILE.capitalize()}',
            'memory'
        )
        self.isos_time_id = layer_time.id()
        layer_time_pr = layer_time.dataProvider()
        layer_time_pr.addAttributes(self.isochrones.get_fields())
        layer_time.updateFields()

        # layer_dist = QgsVectorLayer(
        #     f'{geometry_param}?crs=EPSG:4326',
        #     f'Isodistances {self.PROFILE.capitalize()}',
        #     'memory'
        # )
        # self.isos_dist_id = layer_dist.id()
        # layer_dist_pr = layer_dist.dataProvider()
        # layer_dist_pr.addAttributes(self.isochrones.get_fields())
        # layer_dist.updateFields()

        layer_snapped_points = QgsVectorLayer(
            f'MultiPoint?crs=EPSG:4326',
            f'Snapped Points {self.PROFILE.capitalize()}',
            'memory'
        )
        self.points_snapped_id = layer_snapped_points.id()
        layer_snapped_points_pr = layer_snapped_points.dataProvider()
        layer_snapped_points_pr.addAttributes(self.isochrones.get_point_fields())
        layer_snapped_points.updateFields()

        layer_input_points = QgsVectorLayer(
            f'Point?crs=EPSG:4326',
            f'Input Points {self.PROFILE.capitalize()}',
            'memory'
        )
        self.points_input_id = layer_input_points.id()
        layer_input_points_pr = layer_input_points.dataProvider()
        layer_input_points_pr.addAttributes(self.isochrones.get_point_fields())
        layer_input_points.updateFields()

        denoise = self.parameterAsDouble(parameters, self.IN_DENOISE, context)
        if denoise:
            params[self.IN_DENOISE] = denoise

        generalize = self.parameterAsDouble(parameters, self.IN_GENERALIZE, context)
        if generalize:
            params[self.IN_GENERALIZE] = generalize

        avoid_layer = self.parameterAsLayer(
            parameters,
            self.IN_AVOID,
            context
        )
        if avoid_layer:
            params['avoid_locations'] = get_avoid_locations(avoid_layer)

        show_locations = self.parameterAsBool(parameters, self.IN_SHOW_LOCATIONS, context)

        # Sets all advanced parameters as attributes of self.costing_options
        self.costing_options.set_costing_options(self, parameters, context)

        intervals_time = self.parameterAsString(parameters, self.IN_INTERVALS_TIME, context)
        # intervals_distance = self.parameterAsString(parameters, self.IN_INTERVALS_DISTANCE, context)

        feat_count = source.featureCount() if not intervals_time else source.featureCount() * 2

        self.intervals = {
            "time": [{"time": int(x)} for x in intervals_time.split(',')] if intervals_time else [],
            # "distance": [{"distance": int(x)} for x in intervals_distance.split(',')] if intervals_distance else []
        }

        counter = 0

        for metric, interv in self.intervals.items():
            if feedback.isCanceled():
                break
            if not interv:
                continue
            # Make the actual requests
            requests = []
            for properties in self.get_sorted_feature_parameters(source):
                if feedback.isCanceled():
                    break
                r_params = deepcopy(params)
                r_params['contours'] = interv
                # Get transformed coordinates and feature
                locations, feat = properties
                r_params.update(get_directions_params(locations, self.PROFILE, self.costing_options))
                r_params['id'] = feat[id_field_name]
                requests.append(r_params)

            for params in requests:
                counter += 1
                if feedback.isCanceled():
                    break
                # If feature causes error, report and continue with next
                try:
                    # Populate features from response
                    response = clnt.request('/isochrone', post_json=params)
                except (exceptions.ApiError) as e:
                    msg = "Feature ID {} caused a {}:\n{}".format(
                        params['id'],
                        e.__class__.__name__,
                        str(e))
                    feedback.reportError(msg)
                    logger.log(msg, 2)
                    continue
                except (exceptions.InvalidKey, exceptions.GenericServerError) as e:
                    msg = "{}:\n{}".format(
                        e.__class__.__name__,
                        str(e))
                    feedback.reportError(msg)
                    logger.log(msg)
                    raise

                options = {}
                if params.get('costing_options'):
                    options = params['costing_options']

                self.isochrones.set_response(response)
                for isochrone in self.isochrones.get_features(params['id'], options.get(self.PROFILE)):
                    if metric == 'time':
                        layer_time_pr.addFeature(isochrone)
                    # elif metric == 'distance':
                    #     layer_dist_pr.addFeature(isochrone)

                if show_locations:
                    for point_feat in self.isochrones.get_multipoint_features(params['id']):
                        layer_snapped_points_pr.addFeature(point_feat)
                    for point_feat in self.isochrones.get_point_features(params['id']):
                        layer_input_points_pr.addFeature(point_feat)

                feedback.setProgress(int((counter / feat_count) * 100))

        temp = []
        if layer_time.hasFeatures():
            layer_time.updateExtents()
            context.temporaryLayerStore().addMapLayer(layer_time)
            temp.append(("Isochrones " + self.PROFILE.capitalize(), self.OUT_TIME, layer_time.id()))
        # if layer_dist.hasFeatures():
        if show_locations:
            layer_snapped_points.updateExtents()
            context.temporaryLayerStore().addMapLayer(layer_snapped_points)
            temp.append(("Snapped Points " + self.PROFILE.capitalize(), self.POINTS_SNAPPED, layer_snapped_points.id()))
            layer_input_points.updateExtents()
            context.temporaryLayerStore().addMapLayer(layer_input_points)
            temp.append(("Input Points " + self.PROFILE.capitalize(), self.POINTS_INPUT, layer_input_points.id()))

        results = dict()
        for l_name, e_id, l_id in temp:
            results[e_id] = l_id
            context.addLayerToLoadOnCompletion(
                l_id,
                QgsProcessingContext.LayerDetails(l_name,
                                                  context.project(),
                                                  l_name))

        return results

    def postProcessAlgorithm(self, context, feedback):
        """Style polygon layer in post-processing step."""
        result = dict()
        for metric in self.intervals:
            if metric == 'time':
                layer_id = self.isos_time_id
                out_id = self.OUT_TIME
            else:
                layer_id = self.isos_dist_id
                out_id = self.OUT_DISTANCE
            processed_layer = QgsProcessingUtils.mapLayerFromString(layer_id, context)

            if processed_layer:
                self.isochrones.stylePoly(processed_layer, metric)
                result[out_id] = layer_id

        return result

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

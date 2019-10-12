import inspect

from qgis.core import QgsPointXY, QgsWkbTypes

from valhalla.utils import transform
from .costing_params import CostingAuto

def get_directions_params(points, profile, costing_options):
    """

    :param points: Point list
    :type points: list of QgsPointXY

    :param profile: transportation profile
    :type profile: str

    :param costing_options: costing options class with costing options as attributes
    :type costing_options: CostingAuto

    :returns: dict of Vahalla directions parameters
    :rtype: dict
    """
    params = dict(
        costing=profile,
    )
    params['costing'] = profile
    params['locations'] = get_locations(points)

    costing_params = get_costing_options(costing_options, profile)

    if costing_params:
        params['costing_options'] = costing_params

    return params

def get_locations(points):
    """

    :param points: List of QgsPointXY
    :type points: list of QgsPointXY

    :returns: Valhalla locations list
    :rtype: list of dict
    """

    return [{"lon": round(point.x(), 6), "lat": round(point.y(), 6)} for point in points]


def get_costing_options(costing_options, profile):
    """

    :param costing_options: costing options class with costing options as attributes
    :type costing_options: CostingAuto

    :returns: profile specific costing options
    :rtype: dict of dict
    """
    params = dict()

    costing_options = inspect.getmembers(costing_options, lambda a:not(inspect.isroutine(a)))
    costing_options = [a for a in costing_options if not(a[0].startswith('__') and a[0].endswith('__'))]
    if any([cost[1] for cost in costing_options]):
        params[profile] = dict()
        for cost in costing_options:
            if cost[1]:
                params[profile][cost[0]] = cost[1]

    return params


def get_avoid_locations(avoid_layer):
    """

    :param avoid_layer: The point layer to be avoided
    :type avoid_layer: QgsProcessingFeatureSource

    :returns: Valhalla formatted locations list
    :rtype: list of dict
    """

    locations = []
    xformer_avoid = transform.transformToWGS(avoid_layer.sourceCrs())
    if avoid_layer.wkbType() != QgsWkbTypes.MultiPoint:
        points = []
        for feat in avoid_layer.getFeatures():
            points.append(xformer_avoid.transform(QgsPointXY(feat.geometry().asPoint())))

        for point in points:
            locations.append({"lon": round(point.x(), 6), "lat": round(point.y(), 6)})

    return locations

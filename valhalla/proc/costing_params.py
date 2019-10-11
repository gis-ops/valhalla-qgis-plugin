from qgis.core import (QgsProcessingParameterNumber,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterBoolean)

from valhalla.common import AUTO_COSTING, TRUCK_COSTING, BICYCLE_COSTING, PED_COSTING, BICYCLE_TYPES

class CostingAuto():

    def set_costing_options(self, proc_algo, parameters, context):
        """

        :param proc_algo: Processing algorithm instance
        :type proc_algo: QgsProcessingAlgorithm
        """
        ints = [
            AUTO_COSTING.PENALTY_MANEUVER,
            AUTO_COSTING.PENALTY_TOLL_BOOTH,
            AUTO_COSTING.PENALTY_BORDERS,
            AUTO_COSTING.COST_TOLL_BOOTH,
            AUTO_COSTING.COST_BORDERS,
            AUTO_COSTING.COST_GATES,
            AUTO_COSTING.COST_FERRY,
        ]
        floats = [
            AUTO_COSTING.USE_FERRY,
            AUTO_COSTING.USE_HIGHWAYS,
            AUTO_COSTING.USE_TOLLS,
        ]

        for costing in ints:
            setattr(
                self,
                costing,
                proc_algo.parameterAsInt(
                    parameters,
                    costing,
                    context
                )
            )

        for costing in floats:
            setattr(
                self,
                costing,
                proc_algo.parameterAsDouble(
                    parameters,
                    costing,
                    context
                )
            )

    @staticmethod
    def get_costing_params():
        costings = []

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_MANEUVER,
                description="Penalty for maneuvers",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_BORDERS,
                description="Penalty for border crossings",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_TOLL_BOOTH,
                description="Penalty for toll booths",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_FERRY,
                description="Extra cost for ferry",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_GATES,
                description="Extra cost for gates",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_BORDERS,
                description="Extra cost for crossing borders",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_TOLL_BOOTH,
                description="Extra cost for toll booths",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_HIGHWAYS,
                description="Highway preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_FERRY,
                description="Ferry preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_HIGHWAYS,
                description="Toll road preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        return costings


class CostingTruck:

    def set_costing_options(self, proc_algo, parameters, context):
        """

        :param proc_algo: Processing algorithm instance
        :type proc_algo: QgsProcessingAlgorithm
        """
        ints = [
            AUTO_COSTING.PENALTY_MANEUVER,
            AUTO_COSTING.PENALTY_TOLL_BOOTH,
            AUTO_COSTING.PENALTY_BORDERS,
            AUTO_COSTING.COST_TOLL_BOOTH,
            AUTO_COSTING.COST_BORDERS,
            AUTO_COSTING.COST_GATES,
            AUTO_COSTING.COST_FERRY,
        ]
        floats = [
            AUTO_COSTING.USE_FERRY,
            AUTO_COSTING.USE_HIGHWAYS,
            AUTO_COSTING.USE_TOLLS,
            TRUCK_COSTING.HEIGHT,
            TRUCK_COSTING.WIDTH,
            TRUCK_COSTING.LENGTH,
            TRUCK_COSTING.AXLE_LOAD,
            TRUCK_COSTING.WEIGHT
        ]

        for costing in ints:
            setattr(
                self,
                costing,
                proc_algo.parameterAsInt(
                    parameters,
                    costing,
                    context
                )
            )

        for costing in floats:
            setattr(
                self,
                costing,
                proc_algo.parameterAsDouble(
                    parameters,
                    costing,
                    context
                )
            )

        # Boolean hazmat
        setattr(
            self,
            TRUCK_COSTING.HAZMAT,
            proc_algo.parameterAsBool(
                parameters,
                TRUCK_COSTING.HAZMAT,
                context
            )
        )

    @staticmethod
    def get_costing_params():
        costings = []

        costings.append(
            QgsProcessingParameterNumber(
                name=TRUCK_COSTING.LENGTH,
                description="Total truck length (in m)",
                type=QgsProcessingParameterNumber.Double,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=TRUCK_COSTING.WIDTH,
                description="Total truck width (in m)",
                type=QgsProcessingParameterNumber.Double,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=TRUCK_COSTING.HEIGHT,
                description="Total truck height (in m)",
                type=QgsProcessingParameterNumber.Double,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=TRUCK_COSTING.WEIGHT,
                description="Total truck weight (in tons)",
                type=QgsProcessingParameterNumber.Double,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=TRUCK_COSTING.AXLE_LOAD,
                description="Axle load (in tons)",
                type=QgsProcessingParameterNumber.Double,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterBoolean(
                name=TRUCK_COSTING.HAZMAT,
                description="Hazardous materials",
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_MANEUVER,
                description="Penalty for maneuvers",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_BORDERS,
                description="Penalty for border crossings",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.PENALTY_TOLL_BOOTH,
                description="Penalty for toll booths",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_FERRY,
                description="Extra cost for ferry",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_GATES,
                description="Extra cost for gates",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_BORDERS,
                description="Extra cost for crossing borders",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.COST_TOLL_BOOTH,
                description="Extra cost for toll booths",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_HIGHWAYS,
                description="Highway preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_FERRY,
                description="Ferry preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=AUTO_COSTING.USE_HIGHWAYS,
                description="Toll road preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        return costings


class CostingBicycle:

    def set_costing_options(self, proc_algo, parameters, context):
        """

        :param proc_algo: Processing algorithm instance
        :type proc_algo: QgsProcessingAlgorithm
        """
        ints = [
            BICYCLE_COSTING.SPEED,
            BICYCLE_COSTING.PENALTY_MANEUVER,
            BICYCLE_COSTING.PENALTY_BORDERS,
            BICYCLE_COSTING.COST_GATES,
            BICYCLE_COSTING.COST_BORDERS,
        ]
        floats = [
            BICYCLE_COSTING.USE_FERRY,
            BICYCLE_COSTING.AVOID_SURFACE,
            BICYCLE_COSTING.USE_HILLS,
            BICYCLE_COSTING.USE_ROADS,
        ]

        for costing in ints:
            setattr(
                self,
                costing,
                proc_algo.parameterAsInt(
                    parameters,
                    costing,
                    context
                )
            )

        for costing in floats:
            setattr(
                self,
                costing,
                proc_algo.parameterAsDouble(
                    parameters,
                    costing,
                    context
                )
            )

        # Set bicycle type
        setattr(
            self,
            BICYCLE_COSTING.TYPE,
            proc_algo.parameterAsString(
                parameters,
                BICYCLE_COSTING.TYPE,
                context
            )
        )

    @staticmethod
    def get_costing_params():
        costings = []

        costings.append(
            QgsProcessingParameterEnum(
                name=BICYCLE_COSTING.TYPE,
                description="Bicycle type",
                options=BICYCLE_TYPES,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.SPEED,
                description="Average speed in KPH",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.PENALTY_MANEUVER,
                description="Penalty for maneuvers",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.PENALTY_BORDERS,
                description="Penalty for border crossings",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.COST_GATES,
                description="Extra cost for gates",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.COST_BORDERS,
                description="Extra cost for crossing borders",
                type=QgsProcessingParameterNumber.Integer,
                maxValue=1000,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.USE_FERRY,
                description="Ferry preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.USE_ROADS,
                description="Higher class roads preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.USE_HILLS,
                description="Hills preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.USE_FERRY,
                description="Ferry preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=BICYCLE_COSTING.AVOID_SURFACE,
                description="Bad surface avoidance",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        return costings


class CostingPedestrian:

    def set_costing_options(self, proc_algo, parameters, context):
        """

        :param proc_algo: Processing algorithm instance
        :type proc_algo: QgsProcessingAlgorithm
        """
        ints = [
            PED_COSTING.SPEED,
        ]
        floats = [
            PED_COSTING.USE_FERRY,
            PED_COSTING.FACTOR_ALLEY,
            PED_COSTING.FACTOR_DRIVEWAY,
            PED_COSTING.FACTOR_WALKWAY
        ]

        for costing in ints:
            setattr(
                self,
                costing,
                proc_algo.parameterAsInt(
                    parameters,
                    costing,
                    context
                )
            )

        for costing in floats:
            setattr(
                self,
                costing,
                proc_algo.parameterAsDouble(
                    parameters,
                    costing,
                    context
                )
            )

        # Set max difficulty
        setattr(
            self,
            PED_COSTING.MAX_DIFF,
            int(proc_algo.parameterAsInt(
                parameters,
                PED_COSTING.MAX_DIFF,
                context
            ))
        )

    @staticmethod
    def get_costing_params():
        costings = []

        costings.append(
            QgsProcessingParameterNumber(
                name=PED_COSTING.SPEED,
                description="Walking speed",
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
                maxValue=100,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterEnum(
                name=PED_COSTING.MAX_DIFF,
                description='Maximum hiking difficulty ("sac_value")',
                options=[str(x) for x in range(7)],
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=PED_COSTING.USE_FERRY,
                description="Ferry preference",
                type=QgsProcessingParameterNumber.Double,
                maxValue=1.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=PED_COSTING.FACTOR_DRIVEWAY,
                description="Drive cost factor",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.1,
                maxValue=1000.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=PED_COSTING.FACTOR_WALKWAY,
                description="Walkway cost factor",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.1,
                maxValue=1000.0,
                optional=True,
            )
        )

        costings.append(
            QgsProcessingParameterNumber(
                name=PED_COSTING.FACTOR_ALLEY,
                description="Walkway cost factor",
                type=QgsProcessingParameterNumber.Double,
                minValue=0.1,
                maxValue=1000.0,
                optional=True,
            )
        )

        return costings

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
import datetime
import json
import webbrowser
from shutil import which

from qgis.PyQt.QtWidgets import (QAction,
                             QDialog,
                             QApplication,
                             QMenu,
                             QMessageBox,
                             QDialogButtonBox,
                             QInputDialog,
                             QAbstractButton)
from qgis.PyQt.QtGui import QIcon, QTextDocument
from qgis.PyQt.QtCore import QSizeF, QPointF, Qt

from qgis.core import (QgsProject,
                       QgsVectorLayer,
                       QgsTextAnnotation,
                       QgsMapLayerProxyModel)
from qgis.gui import QgsMapCanvasAnnotationItem
import processing

from . import resources_rc, trace_attributes_gui

from .. import RESOURCE_PREFIX, PLUGIN_NAME, DEFAULT_COLOR, __version__, __email__, __web__, __help__
from ..utils import exceptions, maptools, logger, configmanager, transform
from ..common import client, directions_core, isochrones_core, matrix_core, gravity_core, trace_attributes_core
from ..gui import directions_gui, isochrones_gui, matrix_gui, locate_gui, identify_gui
from ..gui.common_gui import get_locations

from .ValhallaDialogUI_ui import Ui_ValhallaDialogBase
from .ValhallaDialogConfig import ValhallaDialogConfigMain
from .ValhallaDialogLocate import ValhallaDialogLocateMain
from .ValhallaExtraParamsDialog import ValhallaDialogExtraParams


def on_config_click(parent):
    """Pop up provider config window. Outside of classes because it's accessed by multiple dialogs.

    :param parent: Sets parent window for modality.
    :type parent: QDialog
    """
    config_dlg = ValhallaDialogConfigMain(parent=parent)
    config_dlg.exec_()


def on_help_click():
    """Open help URL from button/menu entry."""
    webbrowser.open(__help__)


def on_about_click(parent):
    """Slot for click event of About button/menu entry."""

    info = 'Provides access to <a href="https://github.com/valhalla/valhalla" style="color: {0}">Valhalla</a> routing functionalities.<br><br>' \
           '<center>' \
           '<a href=\"https://gis-ops.com\"><img src=\":/plugins/Valhalla/img/logo_gisops_300.png\"/></a> <br><br>' \
           '</center>' \
           'Author: Nils Nolde<br>' \
           'Email: <a href="mailto:Nils Nolde <{1}>">{1}</a><br>' \
           'Web: <a href="{2}">{2}</a><br>' \
           'Repo: <a href="https://github.com/gis-ops/valhalla-qgis-plugin">github.com/gis-ops/valhalla-qgis-plugin</a><br>' \
           'Version: {3}'.format(DEFAULT_COLOR, __email__, __web__, __version__)

    QMessageBox.information(
        parent,
        'About {}'.format(PLUGIN_NAME),
        info
    )


class ValhallaDialogMain:
    """Defines all mandatory QGIS things about dialog."""

    def __init__(self, iface):
        """

        :param iface: the current QGIS interface
        :type iface: Qgis.Interface
        """
        self.iface = iface
        self.project = QgsProject.instance()

        self.first_start = True
        # Dialogs
        self.dlg = None
        self.menu = None
        self.actions = None

    def initGui(self):
        """Called when plugin is activated (on QGIS startup or when activated in Plugin Manager)."""

        def create_icon(f):
            """
            internal function to create action icons

            :param f: file name of icon.
            :type f: str

            :returns: icon object to insert to QAction
            :rtype: QIcon
            """
            return QIcon(RESOURCE_PREFIX + f)

        icon_plugin = create_icon('icon_valhalla.png')

        self.actions = [
            QAction(
                icon_plugin,
                PLUGIN_NAME,  # tr text
                self.iface.mainWindow()  # parent
            ),
            # Config dialog
            QAction(
                create_icon('icon_settings.png'),
                'Provider Settings',
                self.iface.mainWindow()
            ),
            # About dialog
            QAction(
                create_icon('icon_about.png'),
                'About',
                self.iface.mainWindow()
            ),
            # Help page
            QAction(
                create_icon('icon_help.png'),
                'Help',
                self.iface.mainWindow()
            )

        ]

        # Create menu
        self.menu = QMenu(PLUGIN_NAME)
        self.menu.setIcon(icon_plugin)
        self.menu.addActions(self.actions)

        # Add menu to Web menu and make sure it exsists and add icon to toolbar
        self.iface.addPluginToWebMenu("_tmp", self.actions[2])
        self.iface.webMenu().addMenu(self.menu)
        self.iface.removePluginWebMenu("_tmp", self.actions[2])
        self.iface.addWebToolBarIcon(self.actions[0])

        # Connect slots to events
        self.actions[0].triggered.connect(self._init_gui_control)
        self.actions[1].triggered.connect(lambda: on_config_click(parent=self.iface.mainWindow()))
        self.actions[2].triggered.connect(lambda: on_about_click(parent=self.iface.mainWindow()))
        self.actions[3].triggered.connect(on_help_click)

    def unload(self):
        """Called when QGIS closes or plugin is deactivated in Plugin Manager"""

        self.iface.webMenu().removeAction(self.menu.menuAction())
        self.iface.removeWebToolBarIcon(self.actions[0])
        QApplication.restoreOverrideCursor()
        del self.dlg

    def _cleanup_annotations(self):
        """When window is closed without calculating, clean up annotations"""

        if hasattr(self, 'dlg'):
            for a in self.dlg.annotations:
                self.project.annotationManager().removeAnnotation(a)
            self.dlg.annotations = []

    def _init_gui_control(self):
        """Slot for main plugin button. Initializes the GUI and shows it."""

        # Only populate GUI if it's the first start of the plugin within the QGIS session
        # If not checked, GUI would be rebuilt every time!
        if self.first_start:
            self.first_start = False
            self.dlg = ValhallaDialog(self.iface, self.iface.mainWindow())  # setting parent enables modal view
            # Make sure plugin window stays open when OK is clicked by reconnecting the accepted() signal
            self.dlg.global_buttons.accepted.disconnect(self.dlg.accept)
            self.dlg.global_buttons.accepted.connect(self.run_gui_control)
            self.dlg.global_buttons.rejected.connect(self._cleanup_annotations)
            self.dlg.avoidlocation_dropdown.setFilters(QgsMapLayerProxyModel.PointLayer)
            self.dlg.avoidpolygons_dropdown.setFilters(QgsMapLayerProxyModel.PolygonLayer)

            providers = configmanager.read_config()['providers']
            self.dlg.provider_combo.clear()
            for provider in providers:
                self.dlg.provider_combo.addItem(provider['name'], provider)

        # Populate provider box on window startup, since can be changed from multiple menus/buttons

        self.dlg.show()

    def run_gui_control(self):
        """Slot function for OK button of main dialog."""

        self.dlg: ValhallaDialog

        # Associate annotations with map layer, so they get deleted when layer is deleted
        for annotation in self.dlg.annotations:
            # Has the potential to be pretty cool: instead of deleting, associate with mapLayer, you can change order after optimization
            # Then in theory, when the layer is remove, the annotation is removed as well
            # Doesng't work though, the annotations are still there when project is re-opened
            # annotation.setMapLayer(layer_out)
            self.project.annotationManager().removeAnnotation(annotation)
        self.dlg.annotations = []

        provider_id = self.dlg.provider_combo.currentIndex()
        provider = configmanager.read_config()['providers'][provider_id]

        # if there are no coordinates, throw an error message
        if not self.dlg.routing_fromline_list.count():
            QMessageBox.critical(
                self.dlg,
                "No waypoints",
                """
                Did you forget to set routing waypoints?<br><br>
                
                Use the 'Add Waypoint' button to add up to 20 waypoints.
                """
            )
            return

        # if no API key is present, when ORS is selected, throw an error message
        if not provider['key'] and provider['base_url'].startswith('https://api.openrouteservice.org'):
            QMessageBox.critical(
                self.dlg,
                "Missing API key",
                """
                Did you forget to set an <b>API key</b> for Mapbox?<br><br>
                
                If you don't have an API key, please visit https://account.mapbox.com/auth/signup/?route-to="/" to get one. <br><br>
                Then enter the API key in Web ► Valhalla ► Provider Settings or the settings symbol in the main Valhalla GUI, next to the provider dropdown.
                """
            )
            return

        clnt = client.Client(provider)
        clnt_msg = ''

        method = self.dlg.routing_method.currentText()
        profile = self.dlg.routing_travel_combo.currentText()
        params = {}
        # Add extra params
        extra_params_text = self.dlg.dlg_params.extra_params_text.toPlainText()
        extra_params = {}
        if extra_params_text:
            extra_params = json.loads(extra_params_text)
        # get the timing info
        time_params = dict()
        if self.dlg.routing_time_options_group.isChecked():
            date_time = datetime.datetime.now().replace(second=0, microsecond=0).isoformat(timespec="minutes")
            py_date = self.dlg.datetime_date.dateTime().toPyDateTime()
            py_time = self.dlg.datetime_time.dateTime().toPyDateTime()
            time_type = 0  # right now, ie realtime
            if self.dlg.datetime_departure.isChecked():
                time_type = 1
                date_time = py_date.strftime("%Y-%m-%d") + "T" + py_time.strftime("%H:%M")
            elif self.dlg.datetime_arrival.isChecked():
                time_type = 2
                date_time = py_date.strftime("%Y-%m-%d") + "T" + py_time.strftime("%H:%M")
            time_params = {"date_time": {
                "type": time_type,
                "value": date_time
            }}
        try:
            if method == 'route':
                layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", f"Route {profile.capitalize()}", "memory")
                layer_out.dataProvider().addAttributes(directions_core.get_fields())
                layer_out.updateFields()

                directions = directions_gui.Directions(self.dlg)
                params = directions.get_parameters()
                params.update(extra_params)
                params.update(time_params)
                response = clnt.request('/route', {}, post_json=params)
                feat = directions_core.get_output_feature_directions(
                    response,
                    profile,
                    directions.costing_options,
                    "{}, {}".format(params['locations'][0]['lon'], params['locations'][0]['lat']),
                    "{}, {}".format(params['locations'][-1]['lon'], params['locations'][-1]['lat'])
                )
                layer_out.dataProvider().addFeature(feat)
                layer_out.updateExtents()
                self.project.addMapLayer(layer_out)

            elif method == 'isochrone':
                geometry_type = self.dlg.polygons.currentText()
                isochrones = isochrones_core.Isochrones()
                isochrones.set_parameters(profile, geometry_type)
                locations = get_locations(self.dlg.routing_fromline_list)

                aggregate = self.dlg.iso_aggregate.isChecked()
                locations = [locations] if aggregate else locations

                no_points = self.dlg.iso_no_points.isChecked()

                metrics = []
                if self.dlg.contours_distance.text():
                    metrics.append('distance')
                if self.dlg.contours.text():
                    metrics.append('time')

                for metric in metrics:
                    isochrones_ui = isochrones_gui.Isochrones(self.dlg)
                    params = isochrones_ui.get_parameters(metric)  # change once isodistances are there too
                    params.update(extra_params)
                    params.update(time_params)

                    name = 'Isodistance' if metric == 'distance' else 'Isochrone'
                    layer_out = QgsVectorLayer(f"{geometry_type}?crs=EPSG:4326", f"{name} {params['costing']}", "memory")
                    layer_out.dataProvider().addAttributes(isochrones.get_fields())
                    layer_out.updateFields()

                    for i, location in enumerate(locations):
                        params['locations'] = location if aggregate else [location]
                        isochrones.set_response(clnt.request('/isochrone', {}, post_json=params))
                        for feat in isochrones.get_features(str(i), isochrones_ui.costing_options):
                            layer_out.dataProvider().addFeature(feat)

                    layer_out.updateExtents()
                    self.project.addMapLayer(layer_out)

                if not no_points:
                    multipoint_layer = QgsVectorLayer("MultiPoint?crs=EPSG:4326", f"Snapped Points {params['costing']}", "memory")
                    point_layer = QgsVectorLayer("Point?crs=EPSG:4326", f"Input Points {params['costing']}", "memory")

                    multipoint_layer.dataProvider().addAttributes(isochrones.get_point_fields())
                    multipoint_layer.updateFields()
                    point_layer.dataProvider().addAttributes(isochrones.get_point_fields())
                    point_layer.updateFields()

                    for feat in isochrones.get_multipoint_features('0'):
                        multipoint_layer.dataProvider().addFeature(feat)
                    for feat in isochrones.get_point_features('0'):
                        point_layer.dataProvider().addFeature(feat)
                    multipoint_layer.updateExtents()
                    point_layer.updateExtents()
                    self.project.addMapLayer(multipoint_layer)
                    self.project.addMapLayer(point_layer)

            elif method == 'sources_to_targets':
                matrix_geometries = self.dlg.matrix_geometries.isChecked()
                layer_out = QgsVectorLayer("LineString?crs=EPSG:4326" if matrix_geometries else "None", f'Matrix {profile.capitalize()}', "memory")
                layer_out.dataProvider().addAttributes(matrix_core.get_fields())
                layer_out.updateFields()

                matrix = matrix_gui.Matrix(self.dlg)
                params = matrix.get_parameters()
                params.update(extra_params)
                params.update(time_params)
                if matrix_geometries:
                    params["shape_format"] = "polyline6"
                response = clnt.request('/sources_to_targets', post_json=params)
                feats = matrix_core.get_output_features_matrix(
                    response,
                    profile,
                    matrix.costing_options,
                    matrix_geometries
                )
                for feat in feats:
                    layer_out.dataProvider().addFeature(feat)

                layer_out.updateExtents()
                self.project.addMapLayer(layer_out)

            elif method == 'locate':
                locate_dlg = ValhallaDialogLocateMain()
                locate_dlg.setWindowTitle('Locate Response')

                locate = locate_gui.Locate(self.dlg)
                params = locate.get_parameters()
                params.update(extra_params)
                response = clnt.request('/locate', post_json=params)

                locate_dlg.responseArrived.emit(json.dumps(response, indent=4))

                locate_dlg.exec_()

            elif method == 'extract-osm':
                if not which('osmium'):
                    QMessageBox.critical(
                        self.dlg,
                        "ModuleNotFoundError",
                        """<a href="https://osmcode.org/osmium-tool/">osmium</a> wasn\'t found in your PATH. <br/><br/>Please install before trying again."""
                    )
                    return
                if not self.dlg.pbf_file.filePath():
                    QMessageBox.critical(
                        self.dlg,
                        "FileNotFoundError",
                        """Seems like you forgot to set a PBF file path in the configuration for the Identity tool."""
                    )
                    return

                identify = identify_gui.Identify(self.dlg)
                params = identify.get_locate_parameters()
                response = clnt.request('/locate', post_json=params)
                way_dict = identify.get_tags(response)

                for way_id in way_dict:
                    way = way_dict[way_id]

                    layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Way " + str(way_id), "memory")
                    layer_out.dataProvider().addAttributes(identify.get_fields(way["tags"]))
                    layer_out.updateFields()

                    feat = identify.get_output_feature(way)
                    layer_out.dataProvider().addFeature(feat)
                    layer_out.updateExtents()

                    self.project.addMapLayer(layer_out)
            elif method == 'centroid [experimental]':
                layer_routes = QgsVectorLayer("LineString?crs=EPSG:4326", f"Centroid Routes {profile}", "memory")
                layer_gravity = QgsVectorLayer("Point?crs=EPSG:4326", f"Centroid Point {profile}", "memory")
                layer_routes.dataProvider().addAttributes(gravity_core.get_fields())
                layer_gravity.dataProvider().addAttributes(gravity_core.get_fields())
                layer_routes.updateFields()
                layer_gravity.updateFields()

                directions = directions_gui.Directions(self.dlg)
                params = directions.get_parameters()
                params.update(extra_params)
                response = clnt.request('/centroid', {}, post_json=params)
                line_feats, point_feat = gravity_core.get_output_feature_gravity(
                    response,
                    profile,
                    directions.costing_options
                )
                layer_routes.dataProvider().addFeatures(line_feats)
                layer_gravity.dataProvider().addFeature(point_feat)

                layer_routes.updateExtents()
                layer_gravity.updateExtents()

                self.project.addMapLayer(layer_routes)
                self.project.addMapLayer(layer_gravity)

            elif method == 'trace_attributes':
                layer_edges = QgsVectorLayer("LineString?crs=EPSG:4326", f"Trace Edges {profile}", "memory")
                layer_points = QgsVectorLayer("Point?crs=EPSG:4326", f"Trace Points {profile}", "memory")
                layer_edges.dataProvider().addAttributes(trace_attributes_core.get_fields('edge'))
                layer_points.dataProvider().addAttributes(trace_attributes_core.get_fields('point'))
                layer_edges.updateFields()
                layer_points.updateFields()

                trace_attributes = trace_attributes_gui.TraceAttributes(self.dlg)
                params = trace_attributes.get_parameters()
                params.update(extra_params)

                response = clnt.request('/trace_attributes', {}, post_json=params)
                edge_feats, point_feats = trace_attributes_core.get_output_features(response)

                layer_edges.dataProvider().addFeatures(edge_feats)
                layer_points.dataProvider().addFeatures(point_feats)
                layer_edges.updateExtents()
                layer_points.updateExtents()

                self.project.addMapLayer(layer_edges)
                self.project.addMapLayer(layer_points)

        except exceptions.Timeout as e:
            msg = "The connection has timed out!"
            logger.log(msg, 2)
            self.dlg.debug_text.setText(msg)
            self._display_error_popup(e)
            return

        except (exceptions.ApiError,
                exceptions.InvalidKey,
                exceptions.GenericServerError) as e:
            msg = (e.__class__.__name__,
                   str(e))

            logger.log("{}: {}".format(*msg), 2)
            clnt_msg += "<b>{}</b>: ({})<br>".format(*msg)
            self._display_error_popup(e)
            return

        except Exception as e:
            msg = [e.__class__.__name__ ,
                   str(e)]
            logger.log("{}: {}".format(*msg), 2)
            clnt_msg += "<b>{}</b>: {}<br>".format(*msg)
            self._display_error_popup(e)
            raise

        finally:
            # Set URL in debug window
            clnt_msg += '<a href="{0}">{0}</a><br>Parameters:<br>{1}<br><b>timing</b>: {2:.3f} secs'.format(clnt.url, json.dumps(params, indent=2), clnt.response_time)
            self.dlg.debug_text.setHtml(clnt_msg)

    def _display_error_popup(self, e):
        QMessageBox.critical(
            self.dlg,
            e.__class__.__name__,
            str(e)
        )


class ValhallaDialog(QDialog, Ui_ValhallaDialogBase):
    """Define the custom behaviour of Dialog"""

    def __init__(self, iface, parent=None):
        """
        :param iface: QGIS interface
        :type iface: QgisInterface

        :param parent: parent window for modality.
        :type parent: QDialog/QApplication
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self._iface = iface
        self._mapCanvas = self._iface.mapCanvas()
        self.project = QgsProject.instance()  # invoke a QgsProject instance

        # Set things around the custom map tool
        self.line_tool = None
        self.last_maptool = None
        self.annotations = []

        # Change OK and Cancel button names
        self.global_buttons.button(QDialogButtonBox.Ok).setText('Apply')
        self.global_buttons.button(QDialogButtonBox.Cancel).setText('Close')

        # Add extra params dialog
        self.dlg_params = ValhallaDialogExtraParams(parent=self)

        #### Set up signals/slots ####

        # Config/Help dialogs
        self.provider_config.clicked.connect(lambda: on_config_click(self))
        self.help_button.clicked.connect(on_help_click)
        self.about_button.clicked.connect(lambda: on_about_click(parent=self._iface.mainWindow()))
        self.provider_refresh.clicked.connect(self._on_prov_refresh_click)
        self.time_button_group.buttonToggled.connect(self._on_time_button_toggle)

        # Routing tab
        self.routing_fromline_map.clicked.connect(self._on_linetool_init)
        self.routing_fromline_clear.clicked.connect(self._on_clear_listwidget_click)
        self.routing_import_locations.clicked.connect(self._on_import_locations_click)

        # Extra params
        self.extra_params_button.clicked.connect(self.dlg_params.exec_)

    def _on_time_button_toggle(self, button: QAbstractButton, is_checked: bool):
        if button.objectName() == "datetime_now" and is_checked:
            self.datetime_date.setEnabled(False)
            self.datetime_time.setEnabled(False)
        elif button.objectName() != "datetime_now" and is_checked:
            self.datetime_date.setEnabled(True)
            self.datetime_time.setEnabled(True)

    def _on_import_locations_click(self):
        """Imports valhalla locations as JSON to location table input"""
        raw_json, ok = QInputDialog.getText(
            self,
            'Import Valhalla locations',
            'Valhalla locations as JSON array',
        )
        if ok:
            j = json.loads(raw_json)
            self.routing_fromline_list.clear()
            for idx, loc in enumerate(j):
                self.routing_fromline_list.addItem("Point {0}: {1:.6f}, {2:.6f}".format(idx, loc['lon'], loc['lat']))

    def _on_prov_refresh_click(self):
        """Populates provider dropdown with fresh list from config.yml"""

        providers = configmanager.read_config()['providers']
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider['name'], provider)

    def _on_clear_listwidget_click(self):
        """Clears the contents of the QgsListWidget and the annotations."""
        items = self.routing_fromline_list.selectedItems()
        if items:
            # if items are selected, only clear those
            for item in items:
                row = self.routing_fromline_list.row(item)
                self.routing_fromline_list.takeItem(row)
                if self.annotations:
                    self.project.annotationManager().removeAnnotation(self.annotations.pop(row))
        else:
            # else clear all items and annotations
            self.routing_fromline_list.clear()
            self._clear_annotations()

    def _linetool_annotate_point(self, point, idx):
        annotation = QgsTextAnnotation()

        c = QTextDocument()
        html = "<strong>" + str(idx) + "</strong>"
        c.setHtml(html)

        annotation.setDocument(c)

        annotation.setFrameSizeMm(QSizeF(5,8))
        annotation.setFrameOffsetFromReferencePointMm(QPointF(5, 5))
        annotation.setMapPosition(point)
        annotation.setMapPositionCrs(self._mapCanvas.mapSettings().destinationCrs())

        return QgsMapCanvasAnnotationItem(annotation, self._iface.mapCanvas()).annotation()

    def _clear_annotations(self):
        """Clears annotations"""
        for annotation in self.annotations:
            if annotation in self.project.annotationManager().annotations():
                self.project.annotationManager().removeAnnotation(annotation)
        self.annotations = []

    def _on_linetool_init(self):
        """Hides GUI dialog, inits line maptool and add items to line list box."""
        self.hide()
        self.routing_fromline_list.clear()
        # Remove all annotations which were added (if any)
        self._clear_annotations()

        self.last_maptool = self._iface.mapCanvas().mapTool()

        self.line_tool = maptools.LineTool(self._iface.mapCanvas())
        self._iface.mapCanvas().setMapTool(self.line_tool)
        self.line_tool.pointDrawn.connect(lambda point, idx: self._on_linetool_map_click(point, idx))
        self.line_tool.doubleClicked.connect(self._on_linetool_map_doubleclick)

    def _on_linetool_map_click(self, point, idx):
        """Adds an item to QgsListWidget and annotates the point in the map canvas"""

        transformer = transform.transformToWGS(self._mapCanvas.mapSettings().destinationCrs())
        point_wgs = transformer.transform(point)
        self.routing_fromline_list.addItem("Point {0}: {1:.6f}, {2:.6f}".format(idx, point_wgs.x(), point_wgs.y()))

        annotation = self._linetool_annotate_point(point, idx)
        self.annotations.append(annotation)
        self.project.annotationManager().addAnnotation(annotation)

    def _on_linetool_map_doubleclick(self):
        """
        Populate line list widget with coordinates, end line drawing and show dialog again.

        :param points_num: number of points drawn so far.
        :type points_num: int
        """

        self.line_tool.pointDrawn.disconnect()
        self.line_tool.doubleClicked.disconnect()
        QApplication.restoreOverrideCursor()
        self.show()
        self._iface.mapCanvas().setMapTool(self.last_maptool)

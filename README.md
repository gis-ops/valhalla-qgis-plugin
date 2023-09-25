# valhalla-qgis-plugin

QGIS Plugin providing access to most of the functions of the open-source Valhalla routing engine.

The tool set includes routing, isochrones and matrix calculations, either interactive in the map canvas or from Point/LineString files within the processing framework. Extensive attributes are set for output files, incl. duration, length and start/end locations.

The plugin accesses remote or local Valhalla HTTP APIs. It has the [FOSSGIS server](https://valhalla.openstreetmap.de/) and `localhost` pre-configured.

If you want to quickly get a local setup, try our Valhalla Docker image: https://github.com/gis-ops/docker-valhalla.

There is a guide on [our blog](https://gis-ops.com/valhalla-qgis-plugin) on how to use this plugin.

In case it's not (yet) available on the main QGIS plugin repository, you can add our URL to your QGIS repositories:
https://qgisrepo.gis-ops.com.

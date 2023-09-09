# MBTA Mapper Project

## Deployed to [mbtamapper.com](https://mbtamapper.com/) or [default domain](https://mbtamapper-beta.azurewebsites.net/)

I built this project using SQLAlchemy.

It essentially builds a sqlite database from a GTFS feed, in part from the static feed loaded every day and in part from the realtime feed. It then uses that database to build a map of the MBTA system, with realtime data, exporting it using flask and using leaflet to render the data.

## Javscript Libraries

I built them in. leaflet and leaflet-markercluster are referenced from a CDN. The rest are local files.

[leaflet](https://leafletjs.com/)

[leaflet-realtime](https://github.com/perliedman/leaflet-realtime)

[leaflet-markercluster](https://github.com/Leaflet/Leaflet.markercluster)

[leaflet-search](https://github.com/stefanocudini/leaflet-search)

[leaflet-fullscreen](https://github.com/brunob/leaflet.fullscreen)


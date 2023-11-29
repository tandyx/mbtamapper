# MBTA Realtime Mapping @ <https://mbtamapper.com/>

I built this project using SQLAlchemy.

It essentially builds a sqlite database from a GTFS feed, in part from the static feed loaded every day and in part from the realtime feed. It then uses that database to build a map of the MBTA system, with realtime data, exporting it using flask and using leaflet to render the data.

It's currently deployed to Azure, but I'm looking to move it to Digital Ocean after I run outta money.

## Linting/Formatting

- Python: Black, Pylint, isort
- Javascript: Prettier
- HTML/CSS: Prettier, HTMLLint

## How to run

### To install JavaScript dependencies

```shell
makedir -p ./static/node_modules
npm install --prefix ./static
```

### To run the app

```shell
pip install --upgrade -r requirements.txt
python main.py
```

## Python Dependencies

- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pandas](https://pandas.pydata.org/)
- [Numpy](https://numpy.org/)
- [Requests](https://requests.readthedocs.io/en/master/)
- [Geojson](https://pypi.org/project/geojson/)
- [Shapely](https://pypi.org/project/Shapely/)
- [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/)
- [Werkzeug](https://pypi.org/project/Werkzeug/)
- [GTFS-Realtime Bindings](https://pypi.org/project/gtfs-realtime-bindings/)
- [schedule](https://pypi.org/project/schedule/)
- [json_api_doc](https://pypi.org/project/json_api_doc/)

## Javscript Libraries

- [leaflet](https://leafletjs.com/)
- [leaflet-markercluster](https://github.com/Leaflet/Leaflet.markercluster)
- [leaflet-locatecontrol](https://github.com/domoritz/leaflet-locatecontrol)
- [leaflet-realtime](https://github.com/perliedman/leaflet-realtime)
- [leaflet-search](https://github.com/stefanocudini/leaflet-search)
- [leaflet-fullscreen](https://github.com/brunob/leaflet.fullscreen)

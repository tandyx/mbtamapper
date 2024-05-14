# [mbtamapper.com](https://mbtamapper.com/)

sqlalchemy + flask + leaflet api/web app with realtime mbta data

## setup

### building

```sh
git clone https://github.com/johan-cho/mbtamapper.git
cd mbtamapper
```

```sh
pip3 install --upgrade -r requirements.txt
cd static && 
  npm install && 
  cd ..
```

### running

debug

```sh
python3 main.py -f & python3 main.py
```

production

```sh
python3 main.py &
python3 -m waitress --listen=*:80 --threads=50 --call main:create_default_app &
wait
```

calling `main.py` with no arguments triggers a build process if there's no geojson data and the database doesn't exist. the `-i` (--import-data) flag forces a rebuild. other flags typically refer to testing the frontend locally, but this should be done with waitress (see [`/start.sh`](start.sh)).

every night at 3am est, the database rebuilds. at 3:30am est, map layers are updated (this is the process that takes a while).

## linting + formatting

check out [`/.github/workflows`](.github/workflows)

- `python`: black, pylint, isort
- `javascript`: prettier
- `html/css`: prettier, webhint

### dependencies

- python: [`/requirements.txt`](requirements.txt)
- javascript: [`/static/package.json`](static/package.json)

## api reference

you could query the database (please don't abuse it)

`/api/<orm>?{param}&{param}&...` - query the orm name with parameters

- `include`: comma separated list of relational fields to include
- `geojson={Any}`: return data in geojson format (default: false); to switch to true, set to any value (e.g. geojson=1)
- `kwargs`: columns/on-load-attrs to filter by; supported: `=`, `<`, `>`, `<=`, `>=`, `!=`, `=null`, `!=null`

`/{route_type}/{vehicles|stops|shapes|parking}` - api used by each route (geojson format only)

this data is already filtered out based on `route_type`; see [`/route_keys.json`](route_keys.json).

- `{vehicles}?include=...,...`: realtime vehicle data
  
  - `include`: optional comma separated list of relational fields to include
- `{stops|shapes|parking}`; doesn't take params and redirects to a static `.geojson` file

### example

`/api/stop?stop_id=place-NEC-2108&include=child_stops,routes`

```json
   [
        {
          "at_street": null,
          "child_stops": [{...}, {...}, {...}],
          "level_id": null,
          "location_type": "1",
          "municipality": "Sharon",
          "on_street": null,
          "parent_station": null,
          "platform_code": null,
          "platform_name": null,
          "routes": [{...}],
          "stop_address": "1 Upland Rd, Sharon, MA 02067",
          "stop_code": null,
          "stop_desc": null,
          "stop_id": "place-NEC-2108",
          "stop_lat": 42.124553,
          "stop_lon": -71.184468,
          "stop_name": "Sharon",
          "stop_url": "https://www.mbta.com/stops/place-NEC-2108",
          "timestamp": 1714269647.1744452,
          "vehicle_type": null,
          "wheelchair_boarding": "1",
          "zone_id": "CR-zone-4"
        }
    ]
```

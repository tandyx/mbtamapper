# [mbtamapper.com](https://mbtamapper.com/)

sqlalchemy + flask + leaflet api/web app with realtime mbta data

![example of the app](/static/img/example.png)

## TODO

- [x] use html templates for 404/index
- [ ] add api ref
- [ ] do the google transit things for predictions with svgs
- [ ] compute bearings client side (maybe)
- [ ] figure out way to compute vehicle positions either client or server-side
- [ ] add option to view past stoptimes/trips for each paine (includes adding an options drawer)

## setup

requires python 3.10+ and node 20+

### building

1. clone the repo

   ```sh
   git clone https://github.com/tandyx/mbtamapper.git
   cd mbtamapper
   ```

2. install python requirements in a virtual environment

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate # windows: . .venv/Scripts/Activate.ps1
   pip3 install --upgrade -r requirements.txt
   ```

3. install frontend dependencies

   ```sh
   cd static && npm install && cd ..
   ```

### running

debug

```sh
python3 app.py -i
```

production

```sh
# see ./deploy.sh
sudo .venv/bin/python3 -m waitress --listen=*:80 --threads=50 --call app:create_main_app &
wait
```

calling `app.py` with no arguments triggers a build process if there's no geojson data and the database doesn't exist. the `-i` (--import-data) flag forces a rebuild.

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
- `cache`: seconds to cache (int, float untested but should work)

> [!NOTE]  
> 2025-07-17: nulls are now culled from the feed

`/{route_type}/{vehicles|stops|shapes|parking}` - api used by each route (geojson format only)

this data is already filtered out based on `route_type`; see [`/route_keys.json`](route_keys.json).

- `/vehicles?include=...,...&cache=...`: realtime vehicle data

  - `include`: optional comma separated list of relational fields to include
  - `cache`: seconds to cache (int, float untested but should work)

- `/{stops|shapes|parking}`; doesn't take params and redirects to a static `.geojson` file

### example

`/api/stop?stop_id=place-NEC-2108&include=child_stops,routes`

```json
[
  {
    "child_stops": [
      {
        "location_type": "0",
        "municipality": "Sharon",
        "parent_station": "place-NEC-2108",
        "platform_name": "Commuter Rail",
        "stop_desc": "Sharon - Commuter Rail",
        "stop_id": "NEC-2108",
        "stop_lat": 42.124553,
        "stop_lon": -71.184468,
        "stop_name": "Sharon",
        "stop_url": "https://www.mbta.com/stops/place-NEC-2108",
        "vehicle_type": "2",
        "wheelchair_boarding": "1",
        "zone_id": "CR-zone-4"
      },
      {
        "location_type": "0",
        "municipality": "Sharon",
        "parent_station": "place-NEC-2108",
        "platform_code": "1",
        "platform_name": "Track 1 (Outbound)",
        "stop_desc": "Sharon - Commuter Rail - Track 1 (Outbound)",
        "stop_id": "NEC-2108-01",
        "stop_lat": 42.124553,
        "stop_lon": -71.184468,
        "stop_name": "Sharon",
        "stop_url": "https://www.mbta.com/stops/place-NEC-2108",
        "vehicle_type": "2",
        "wheelchair_boarding": "1",
        "zone_id": "CR-zone-4"
      },
      {
        "location_type": "0",
        "municipality": "Sharon",
        "parent_station": "place-NEC-2108",
        "platform_code": "2",
        "platform_name": "Track 2 (Boston)",
        "stop_desc": "Sharon - Commuter Rail - Track 2 (Boston)",
        "stop_id": "NEC-2108-02",
        "stop_lat": 42.124553,
        "stop_lon": -71.184468,
        "stop_name": "Sharon",
        "stop_url": "https://www.mbta.com/stops/place-NEC-2108",
        "vehicle_type": "2",
        "wheelchair_boarding": "1",
        "zone_id": "CR-zone-4"
      }
    ],
    "location_type": "1",
    "municipality": "Sharon",
    "routes": [
      {
        "agency_id": "1",
        "line_id": "line-Providence",
        "network_id": "commuter_rail",
        "route_color": "80276C",
        "route_desc": "Regional Rail",
        "route_fare_class": "Commuter Rail",
        "route_id": "CR-Providence",
        "route_long_name": "Providence/Stoughton Line",
        "route_name": "Providence / Stoughton Line",
        "route_sort_order": 20013,
        "route_text_color": "FFFFFF",
        "route_type": "2",
        "route_url": "https://www.mbta.com/schedules/CR-Providence"
      }
    ],
    "stop_address": "1 Upland Rd, Sharon, MA 02067",
    "stop_id": "place-NEC-2108",
    "stop_lat": 42.124553,
    "stop_lon": -71.184468,
    "stop_name": "Sharon",
    "stop_url": "https://www.mbta.com/stops/place-NEC-2108",
    "wheelchair_boarding": "1",
    "zone_id": "CR-zone-4"
  }
]
```

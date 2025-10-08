# [mbtamapper.com](https://mbtamapper.com/)

sqlalchemy + flask + leaflet api/web app with realtime mbta data, including subway, commuter rail (keolis) and buses.tracks live locations, routes and alerts of all mbta lines.

![example of the app](/static/img/example.png)

## TODO

- [x] use html templates for 404/index
- [ ] add api ref
- [ ] add debugging raw js back
- [ ] rate limit API
- [ ] remove `explode_df`
- [x] use bundles for custom js
- [ ] add light on dark and dark on light
- [ ] do the google transit things for predictions with svgs (maybe)
- [ ] compute bearings client side (maybe)
- [ ] figure out way to compute vehicle positions either client or server-side
- [ ] add option to view past stoptimes/trips for each paine (includes adding an options drawer)
- [ ] include shuttles trips within routes
- [ ] WIP: departure board

## setup

requires python 3.12+ and node 18+

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
   npm install
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

### linting + formatting

check out [`/.github/workflows`](.github/workflows)

- `python`: black, pylint, isort
- `javascript`: prettier
- `html/css`: prettier, webhint

### dependencies

- python: [`/requirements.txt`](requirements.txt)
- javascript: [`/package.json`](package.json)

## website operations

### frontend

this frontend uses vanilla javascript/css using esbuild, built around leaflet. until september 2025, it was using completely vanilla javascript with individually-loaded node-modules, but it's faster and less server-load to bundle all the javascript. the disadvantage is that it's harder to debug.

#### query parameters

each vehicle-type-specific route has these query parameters:

- `navless` | `navbarless`: if this parameter exists and is truthy, hide the navbar. iframes are already hidden. this is automatically done if this website is in an iframe.
- `sideless` | `sidebarless`: if this parameter exists and is truthy, don't auto-show the sidebar. this is automatically done if this website is in an iframe.

setting these to true: eg. <https://mbtamapper.com/commuter_rail?navless=true&sideless=true>, may be optimal for digital signage.

#### window hashes

when a marker is clicked, the id of that object is set as the window hash. this enables sharing of a specific location or returning to one after the page has been dormaint.

#### realtime data

leaflet-realtime is used to query the database at a certain interval and automatically refresh the layer. however, because the popup content, etc also has to be refreshed, the codebase became a messy disaster. thus, each realtime layer is wrapped within an encompassing class that limits how many functions I put into the global scope.

### backend

this website operates on a nightly rebuild and persistent scheduler that runs in the background to the flask app. (see [`feed_loader.py`](/backend/gtfs_loader/feed_loader.py)). _more documentation to come_

```python
self.scheduler.add_job(
    self.import_realtime, "interval", args=[Alert], minutes=1
)
self.scheduler.add_job(
    self.import_realtime, "interval", args=[Vehicle], seconds=11
)
self.scheduler.add_job(
    self.import_realtime, "interval", args=[Prediction], seconds=21
)
self.scheduler.add_job(self.geojson_exports, "cron", hour=4, minute=0)
self.scheduler.add_job(self.nightly_import, "cron", hour=3, minute=30)
self.scheduler.add_job(self.clear_caches, "cron", day="*/4", hour=3, minute=40)
self.scheduler.start()
```

## api reference

users could query the database directly (please don't abuse it)

`/api/<orm>?{param}&{param}&...` - query the orm name with parameters

- `include`: comma separated list of relational fields to include
- `geojson={Any}`: return data in geojson format (default: false); to switch to true, set to any value (e.g. geojson=1)
- `kwargs`: columns/on-load-attrs to filter by; supported: `=`, `<`, `>`, `<=`, `>=`, `!=`, `=null`, `!=null`
- `cache`: seconds to cache (int, float untested but should work)

> [!NOTE]  
> 2025-07-17: nulls are now culled from the feed

`/{route_type}/{vehicles|stops|shapes|parking}` - api used by each route (geojson format only)

this data is already filtered out based on `route_type`; see [`/route_keys.json`](/static/config/route_keys.json).

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

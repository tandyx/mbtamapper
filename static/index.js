const ARRAY = [
  "SUBWAY",
  "RAPID_TRANSIT",
  "COMMUTER_RAIL",
  "BUS",
  "FERRY",
  "ALL_ROUTES",
];
window.addEventListener("load", function () {
  L.Map.include({
    _initControlPos: function () {
      var corners = (this._controlCorners = {}),
        l = "leaflet-",
        container = (this._controlContainer = L.DomUtil.create(
          "div",
          l + "control-container",
          this._container
        ));

      function createCorner(vSide, hSide) {
        var className = l + vSide + " " + l + hSide;

        corners[vSide + hSide] = L.DomUtil.create("div", className, container);
      }

      createCorner("top", "left");
      createCorner("top", "right");
      createCorner("bottom", "left");
      createCorner("bottom", "right");

      createCorner("top", "center");
      createCorner("middle", "center");
      createCorner("middle", "left");
      createCorner("middle", "right");
      createCorner("bottom", "center");
    },
  });

  var route_type = ARRAY[Math.floor(Math.random() * ARRAY.length)];
  var zoom = route_type == "COMMUTER_RAIL" ? 11 : 13;
  var map = L.map("map", {
    zoomControl: false,
    maxZoom: zoom,
    minZoom: zoom,
  }).setView([42.3519, -71.0552], zoom);

  map.dragging.disable();
  map.touchZoom.disable();
  map.doubleClickZoom.disable();
  map.scrollWheelZoom.disable();
  map.boxZoom.disable();
  map.keyboard.disable();
  if (map.tap) map.tap.disable();
  document.getElementById("map").style.cursor = "default";

  var CartoDB_Positron = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {
      // attribution:
      //   '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }
  ).addTo(map);
  var CartoDB_DarkMatter = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      // attribution:
      //   '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }
  );

  var shape_layer = L.layerGroup().addTo(map);
  realtime = plotShapes(route_type, shape_layer).addTo(map);

  map.on("click", function (e) {
    // console.log(e.originalEvent.target.offsetParent)
    if (map.hasLayer(CartoDB_Positron)) {
      map.removeLayer(CartoDB_Positron);
      map.addLayer(CartoDB_DarkMatter);
    } else {
      map.removeLayer(CartoDB_DarkMatter);
      map.addLayer(CartoDB_Positron);
    }
  });

  L.Control.textbox = L.Control.extend({
    onAdd: function (map) {
      var text = L.DomUtil.create("div");
      text.id = "info_text";
      text.innerHTML = `
      <div class="main">
          <h1>MBTA Mapper</h1>
          <h4>Realtime Tracking of MBTA Vehicles</h4>
          <h4 style="color:red;">New Domain: mbtamapper.com</h4>
          <table style="margin-left: auto;margin-right: auto;width:auto;">
              <tr>
                  <td>
                      <a href="/subway/" style="font-weight:bold;text-decoration:none;color:#7C878E;">
                          <img src="/static/img/subway.png" width="125"><br><br>
                          Subway
                      </a>
                  </td>
                  <td>
                      <a href="/rapid_transit/" style="font-weight:bold;text-decoration:none;color:#ED8B00;">
                          <img src="/static/img/rapid_transit.png" width="125"><br><br>
                          Rapid Transit
                      </a>
                  </td>
                  <td>
                      <a href="/commuter_rail/" style="font-weight:bold;text-decoration:none;color:#80276C;">
                          <img src="/static/img/commuter_rail.png" width="125"><br><br>
                          Commuter Rail
                      </a>
                  </td>
              </tr>
              <tr>
                  <td>
                      <a href="/bus/" style="font-weight:bold;text-decoration:none;color:#FFC72C;">
                          <img src="/static/img/bus.png" width="125"><br><br>
                          Bus <a style="color:red">(limited to 75 vehicles)</a>
                      </a>
                  </td>
                  <td>
                      <a href="/ferry/" style="font-weight:bold;text-decoration:none;color:#006595;">
                          <img src="/static/img/ferry.png" width="125"><br><br>
                          Ferry <a style="color:red">(no vehicle data)</a>
                      </a>
                  </td>
                  <td>
                      <a href="/all_routes/" style="font-weight:bold;text-decoration:none;color:#ffffff;">
                          <img src="/static/img/mbta.png" width="125"><br><br>
                          All Routes <a style="color:red">(limited to 75 vehicles)</a>
                      </a>
                  </td>
              </tr>
          </table>
          <div style="margin-top:25px">
              This was my personal project. While I used to work for Keolis, I have no further affiliation with the MBTA.<br><br>
              <a href="https://github.com/tandy-c/mbta_mapper" style="font-weight:bold;text-decoration:none;color:#ffffff;padding:15px;">
                  <img src="/static/img/github.jpg" width="45">
              </a>
              <a href="https://www.linkedin.com/in/chojohan/" style="font-weight:bold;text-decoration:none;color:#ffffff;">
                  <img src="/static/img/linkedin.png" width="45">
              </a>
              <a href="https://tandy-c.github.io/website/" style="font-weight:bold;text-decoration:none;color:#ffffff;">
                  <img src = "static/aboutme.png" width="45">
              </a>
          </div>
      </div>
      `;
      return text;
    },

    onRemove: function (map) {
      // Nothing to do here
    },
  });

  L.control.textbox = function (opts) {
    return new L.Control.textbox(opts);
  };
  L.control.textbox({ position: "topcenter" }).addTo(map);
});

// var zoom = route_type == "commuter_rail" ? 9 : 13;

function plotShapes(key, layer) {
  let polyLineRender = L.canvas({ padding: 0, tolerance: 0 });
  return L.realtime(`/static/geojsons/${key}/shapes.json`, {
    interval: 360000000000000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.setStyle({
        interactive: false,
        color: f.properties.color,
        opacity: f.properties.opacity,
        weight: 1.3,
        renderer: polyLineRender,
      });
    },
  });
}

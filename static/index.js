window.addEventListener("load", function () {
  createMap(
    "map",
    "SUBWAY",
    "RAPID_TRANSIT",
    "COMMUTER_RAIL",
    "BUS",
    "FERRY",
    "ALL_ROUTES"
  );
});

function createMap(id, ...routes) {
  /** map factory function for index.html
   * @param {string} id - id of div to create map in
   * @param {routes} routes - route type routes
   * @returns {L.map} map
   */

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
        /** creates a control container with corners at the map edges
         * @param {string} vSide - vertical side: 'top' or 'bottom'
         * @param {string} hSide - horizontal side: 'left' or 'right'
         * @returns {void}
         */
        const className = l + vSide + " " + l + hSide;
        corners[vSide + hSide] = L.DomUtil.create("div", className, container);
      }

      for (const vpos of ["top", "middle", "bottom"]) {
        for (const hpos of ["left", "center", "right"]) {
          createCorner(vpos, hpos);
        }
      }
    },
  });

  const route_type = routes[Math.floor(Math.random() * routes.length)];
  const zoom = route_type == "COMMUTER_RAIL" ? 11 : 13;
  const map = L.map(id, {
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

  const baseLayers = getBaseLayerDict(
    "CartoDB.PositronNoLabels",
    "CartoDB.DarkMatterNoLabels"
  );
  baseLayers["Light"].addTo(map);

  const shape_layer = L.layerGroup().addTo(map);
  plotShapes(`/static/geojsons/${route_type}/shapes.json`, shape_layer, false);

  map.on("click", function () {
    if (map.hasLayer(baseLayers["Light"])) {
      map.removeLayer(baseLayers["Light"]);
      map.addLayer(baseLayers["Dark"]);
    } else {
      map.removeLayer(baseLayers["Dark"]);
      map.addLayer(baseLayers["Light"]);
    }
  });

  L.Control.textbox = L.Control.extend({
    onAdd: function () {
      var text = L.DomUtil.create("div");
      text.id = "info_text";
      text.innerHTML = `
      <div class="main">
          <h1>MBTA Mapper</h1>
          <h4 class='subheader'>Realtime Tracking of MBTA Vehicles <a href="#" style="color:inherit;">@mbtamapper.com</a></h4>
          <table class="homepage">
              <tr>
                  <td>
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view the subway!</span>
                      <a href="/subway/" style="font-weight:bold;color:#00843d;" onmouseover="hoverImage('subway')" onmouseleave="unhoverImage('subway')">
                          <img src="/static/img/subway.png" width="125" alt="subway" id="subway"><br><br>
                          Subway
                      </a></span>
                  </td>
                  <td>
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view the subway + silver line!</span>
                      <a href="/rapid_transit/" style="font-weight:bold;color:#DA291C;" onmouseover="hoverImage('rapid_transit')" onmouseleave="unhoverImage('rapid_transit')">
                          <img src="/static/img/rapid_transit.png" width="125" alt="rapid_transit" id="rapid_transit"><br><br>
                          "Rapid" Transit
                      </a></span>
                  </td>
                  <td>
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view the commuter rail!</span>
                      <a href="/commuter_rail/" style="font-weight:bold;color:#80276C;" onmouseover="hoverImage('commuter_rail')" onmouseleave="unhoverImage('commuter_rail')">
                          <img src="/static/img/commuter_rail.png" width="125" alt="commuter_rail" id="commuter_rail"><br><br>
                          Commuter Rail
                      </a></span>
                  </td>
              </tr>
              <tr>
                  <td>
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view the bus!</span>
                      <a href="/bus/" style="font-weight:bold;color:#FFC72C;" onmouseover="hoverImage('bus')" onmouseleave="unhoverImage('bus')">
                          <img src="/static/img/bus.png" width="125" alt="bus" id="bus"><br><br>
                          Bus <span style="color:red">(limited to 75 vehicles)</span>
                      </a></span>
                  </td>
                  <td>
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view the ferry!</span>
                      <a href="/ferry/" style="font-weight:bold;color:#006595;" onmouseover="hoverImage('ferry')" onmouseleave="unhoverImage('ferry')">
                          <img src="/static/img/ferry.png" width="125"  id="ferry" alt="ferry"><br><br>
                          Ferry <span style="color:red">(no vehicle data)</span>
                      </a></span>
                  </td>
                  <td >
                    <span class = "tooltip">
                    <span class = "tooltiptext" style="top:25%;">Click to view all routes!</span>
                      <a href="/all_routes/" style="font-weight:bold;color:#ffffff;" onmouseover="hoverImage('all_routes')" onmouseleave="unhoverImage('all_routes')">
                          <img src="/static/img/mbta.png" width="125" alt="all_routes" id="all_routes" ><br><br>
                          All Routes <span style="color:red">(limited to 75 vehicles)</span>
                      </a></span>
                  </td>
              </tr>
          </table>
          <div style="margin-top:-10px">
              <h4>This was a personal project. While I used to work for Keolis, I have no further affiliation with the MBTA.</h4>
              <span class = "tooltip-mini_image" style="padding:5px;" onmouseover="hoverImage('github')" onmouseleave="unhoverImage('github')">
              <span class = "tooltiptext-mini_image contacts">View this repository</span>
              <a href="https://github.com/tandy-c/mbta_mapper" >
                  <img src="/static/img/github.png" class="contact_imgs" alt="github" id="github" >
              </a></span>
              <span class = "tooltip-mini_image" style="padding:5px;" onmouseover="hoverImage('about_me')" onmouseleave="unhoverImage('about_me')">
              <span class = "tooltiptext-mini_image contacts">About me!</span>
              <a href="https://tandy-c.github.io/website/" >
                  <img src = "/static/img/johan.png" class="contact_imgs" alt="about_me" id="about_me" >
              </a></span>
              <span class = "tooltip-mini_image" style="padding:5px;" onmouseover="hoverImage('linkedin')" onmouseleave="unhoverImage('linkedin')">
              <span class = "tooltiptext-mini_image contacts">My Linkedin</span>
              <a href="https://www.linkedin.com/in/chojohan/" >
                  <img src = "/static/img/linkedin.png" class="contact_imgs" alt="linkedin" id="linkedin" >
              </a></span>
              <span class = "tooltip-mini_image" style="padding:5px;" onmouseover="hoverImage('facebook')" onmouseleave="unhoverImage('facebook')">
              <span class = "tooltiptext-mini_image contacts">My Facebook</span>
              <a href="https://www.facebook.com/johan.cho.927" >
                  <img src = "/static/img/facebook.png" class="contact_imgs" alt="facebook" id="facebook" >
              </a></span>
              <span class = "tooltip-mini_image" style="padding:5px;" onmouseover="hoverImage('youtube')" onmouseleave="unhoverImage('youtube')">
              <span class = "tooltiptext-mini_image contacts">My Youtube (haven't touched it in a bit)</span>
              <a href="https://www.youtube.com/channel/UCP91LPgRFY03YoIGrmuMH9A" >
                  <img src = "/static/img/youtube.png" class="contact_imgs" alt="youtube" id="youtube" >
              </a></span>
          </div>
      </div>
      `;
      return text;
    },
  });

  L.control.textbox = function (opts) {
    return new L.Control.textbox(opts);
  };
  L.control.textbox({ position: "topcenter" }).addTo(map);

  return map;
}

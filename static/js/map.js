window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0].toUpperCase();
  createMap("map", ROUTE_TYPE);

  document.addEventListener("click", function (event) {
    // Check if the clicked element is not inside the navbar
    if (!event.target.closest(".nav")) {
      // Close the hamburger menu
      let menuToggle = document.getElementById("menu-toggle");
      if (menuToggle.checked) {
        menuToggle.checked = false;
      }
    }
  });
});
/** map factory function for map.html
 * @param {string} id - id of the map div
 * @param {string} route_type - route type
 * @returns {L.map} map
 */
function createMap(id, route_type) {
  const map = L.map(id, {
    minZoom: 9,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: "topleft",
    },
    attributionControl: true,
  }).setView([42.3519, -71.0552], route_type == "COMMUTER_RAIL" ? 10 : 13);

  const baseLayers = getBaseLayerDict(...Array(2), {
    Alt: "Stadia.AlidadeSmoothDark",
  });
  baseLayers["Dark"].addTo(map);

  let stop_layer = L.layerGroup().addTo(map);
  stop_layer.name = "Stops";

  let shape_layer = L.layerGroup().addTo(map);
  shape_layer.name = "Shapes";

  let vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "COMMUTER_RAIL" ? 10 : 12,
  }).addTo(map);
  vehicle_layer.name = "Vehicles";

  let parking_lots = L.layerGroup();
  parking_lots.name = "Parking Lots";

  plotStops(`/${route_type.toLowerCase()}/api/stop`, stop_layer);
  plotShapes(`/static/geojsons/${route_type}/shapes.json`, shape_layer);
  plotVehicles(
    `/${route_type.toLowerCase()}/vehicles?include=route,next_stop,stop_time`,
    vehicle_layer
  );
  plotFacilities(`/static/geojsons/${route_type}/park.json`, parking_lots);

  createControlLayers(
    baseLayers,
    stop_layer,
    shape_layer,
    vehicle_layer,
    parking_lots
  ).forEach((control) => control.addTo(map));

  map.on("zoomend", function () {
    if (map.getZoom() < 16) map.removeLayer(parking_lots);
    if (map.getZoom() >= 16) map.addLayer(parking_lots);
  });

  if (map.hasLayer(parking_lots)) map.removeLayer(parking_lots);

  return map;
}
/** create control layers
 * @param {Object} tile_layers - base layers
 * @param {L.layerGroup} layers - layers to be added to the map
 * @returns {Array} control layers
 */
function createControlLayers(tile_layers, ...layers) {
  const locateControl = L.control.locate({
    enableHighAccuracy: true,
    initialZoomLevel: 15,
    metric: false,
    markerStyle: {
      zIndexOffset: 500,
    },
  });

  const controlSearch = L.control.search({
    layer: L.layerGroup(layers),
    initial: false,
    propertyName: "name",
    zoom: 16,
    marker: false,
    textPlaceholder: "",
  });
  controlSearch.on("search:locationfound", function (event) {
    event.layer.openPopup();
  });

  const layerControl = L.control.layers(
    tile_layers,
    Object.fromEntries(layers.map((layer) => [layer.name, layer]))
  );

  return [locateControl, controlSearch, layerControl];
}

/** Plot stops on map in realtime, updating every hour
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot stops on
 * @returns {L.realtime} - realtime layer
 */

function plotStops(url, layer) {
  const stopIcon = L.icon({
    iconUrl: "static/img/mbta.png",
    iconSize: [12, 12],
  });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.id);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}
/** Plot shapes on map in realtime, updating every hour
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot shapes on
 * @param {boolean} interactive - whether or not to make shapes interactive
 * @returns {L.realtime} - realtime layer
 */
function plotShapes(url, layer, interactive = true) {
  const polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.setStyle({
        color: `#${f.properties.route_color}`,
        opacity: f.properties.opacity,
        weight: 1.3,
        renderer: polyLineRender,
      });
      if (interactive) {
        l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
        l.bindTooltip(f.properties.name);
      }
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}
/** Plot facilities on map in realtime, updating every hour
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot facilities on
 * @returns {L.realtime} - realtime layer
 */
function plotFacilities(url, layer) {
  const facilityIcon = L.icon({
    iconUrl: "static/img/parking.png",
    iconSize: [15, 15],
  });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(facilityIcon);
      l.setZIndexOffset(-150);
    },
  });
  realtime.on("update", handleUpdateEvent);
  return realtime;
}

/** Handle update event for realtime layers
 * @param {L.realtime}
 * @returns {void}
 */
function handleUpdateEvent(entity) {
  Object.keys(entity.update).forEach(
    function (id) {
      const feature = entity.update[id];
      updateLayer.call(this, id, feature);
    }.bind(this)
  );
}

/** Update layer
 * @param {string} id - id of layer to update
 * @param {L.feature}
 * @returns {void}
 */
function updateLayer(id, feature) {
  const layer = this.getLayer(id);
  const wasOpen = layer.getPopup().isOpen();
  layer.unbindPopup();

  if (wasOpen) layer.closePopup();

  layer.bindPopup(feature.properties.popupContent, {
    maxWidth: "auto",
  });

  if (wasOpen) layer.openPopup();
}

/** Get base layer dictionary
 * @summary Get base layer dictionary
 * @param {string} lightId - id of light layer
 * @param {string} darkId - id of dark layer
 * @param {object} additionalLayers - additional layers to add to dictionary
 * @returns {object} - base layer dictionary
 */
function getBaseLayerDict(
  lightId = "CartoDB.Positron",
  darkId = "CartoDB.DarkMatter",
  additionalLayers = {}
) {
  const baseLayers = {
    Light: L.tileLayer.provider(lightId),
    Dark: L.tileLayer.provider(darkId),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}

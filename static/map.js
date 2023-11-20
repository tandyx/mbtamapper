window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0].toUpperCase();
  document.title = "MBTA " + titleCase(ROUTE_TYPE) + " Realtime Map";
  setFavicon(ROUTE_TYPE.toLowerCase());
  document
    .querySelector('meta[name="description"]')
    .setAttribute(
      "content",
      "MBTA Realtime map for the MBTA's " + titleCase(ROUTE_TYPE) + "."
    );

  setNavbar("navbar", ROUTE_TYPE, window.mobileCheck());
  createMap("map", ROUTE_TYPE);
});

function createMap(id, route_type) {
  /** map factory function for map.html
   * @param {string} route_type - route type
   * @returns {L.map} map
   */

  const map = L.map(id, {
    minZoom: 9,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: "topleft",
    },
  }).setView([42.3519, -71.0552], route_type == "COMMUTER_RAIL" ? 10 : 13);

  const positron = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {
      subdomains: "abcd",
      maxZoom: 20,
    }
  ).addTo(map);

  const darkMatter = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      subdomains: "abcd",
      maxZoom: 20,
    }
  );

  const stop_layer = L.layerGroup().addTo(map);
  const shape_layer = L.layerGroup().addTo(map);
  const vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "COMMUTER_RAIL" ? 10 : 12,
  }).addTo(map);
  const parking_lots = L.layerGroup();

  plotStops(`/static/geojsons/${route_type}/stops.json`, stop_layer);
  plotShapes(`/static/geojsons/${route_type}/shapes.json`, shape_layer);
  plotVehicles(`/${route_type.toLowerCase()}/vehicles`, vehicle_layer);
  plotFacilities(`/static/geojsons/${route_type}/park.json`, parking_lots);

  createControlLayers(stop_layer, shape_layer, vehicle_layer, parking_lots)
    .concat(
      L.control.layers(
        {
          Dark: darkMatter,
          Light: positron,
        },
        {
          Vehicles: vehicle_layer,
          Stops: stop_layer,
          Shapes: shape_layer,
          "Parking Lots": parking_lots,
        }
      )
    )
    .forEach((control) => control.addTo(map));

  map.on("zoomend", function () {
    if (map.getZoom() < 16) map.removeLayer(parking_lots);
    if (map.getZoom() >= 16) map.addLayer(parking_lots);
  });

  if (map.hasLayer(parking_lots)) map.removeLayer(parking_lots);

  return map;
}

function createControlLayers(...layers) {
  /** create control layers
   * @param {L.tileLayer[]} tile_layers - tile layers to add to layer control
   * @param {L.layerGroup} layers - layers to be controlled
   * @returns {L.control} control layers
   */

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

  return [locateControl, controlSearch];
}

window.addEventListener("load", function () {
  ROUTE_TYPE = window.location.href.split("/").slice(-2)[0].toUpperCase();
  document.title = "MBTA " + titleCase(ROUTE_TYPE) + " Realtime Map";
  setFavicon(ROUTE_TYPE.toLowerCase());
  document
    .querySelector('meta[name="description"]')
    .setAttribute(
      "content",
      "MBTA Realtime map for the MBTA's " + titleCase(ROUTE_TYPE) + "."
    );

  var mobile = window.mobileCheck();
  setNavbar("navbar", ROUTE_TYPE, mobile);

  // if (this.window.mobileCheck()) {
  //   var body = document.getElementsByTagName("body")[0];
  //   body.style.overflow = "hidden";
  //   body.style.padding = "0";
  //   console.log("Mobile");
  // } else {
  //   console.log("Desktop");
  // }

  var map = createMap(ROUTE_TYPE);
});

function createMap(route_type) {
  var map = L.map("map", {
    minZoom: 9,
    maxZoom: 20,
    // zoomSnap: 0,
    // // zoomDelta: 0.1,
    // // wheelPxPerZoomLevel: 1000,
    // wheelDebounceTime: 5,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: "topleft",
    },
  }).setView([42.3519, -71.0552], route_type == "COMMUTER_RAIL" ? 10 : 13);

  var CartoDB_Positron = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {
      subdomains: "abcd",
      maxZoom: 20,
    }
  ).addTo(map);

  var CartoDB_DarkMatter = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      subdomains: "abcd",
      maxZoom: 20,
    }
  );

  var stop_layer = L.layerGroup().addTo(map);
  var shape_layer = L.layerGroup().addTo(map);
  var vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "COMMUTER_RAIL" ? 10 : 12,
  }).addTo(map);
  var parking_lots = L.layerGroup();

  var stopsRealtime = plotStops(
    `/static/geojsons/${route_type}/stops.json`,
    stop_layer
  ).addTo(map);
  var shapesRealtime = plotShapes(
    `/static/geojsons/${route_type}/shapes.json`,
    shape_layer
  ).addTo(map);
  var vehiclesRealtime = plotVehicles(
    `/${route_type.toLowerCase()}/vehicles`,
    // `/static/geojsons/${ROUTE_TYPE}/vehicles.json`,
    vehicle_layer
  ).addTo(map);
  var facilitiesRealtime = plotFacilities(
    `/static/geojsons/${route_type}/park.json`,
    parking_lots
  );

  var controlLayer = L.layerGroup().setZIndex(50000000).addTo(map);

  var controlLocate = L.control
    .locate({
      layer: controlLayer,
      enableHighAccuracy: true,
      initialZoomLevel: 15,
      metric: false,
    })
    .addTo(map);

  var controlSearch = L.control
    .search({
      layer: L.layerGroup([
        stop_layer,
        shape_layer,
        vehicle_layer,
        parking_lots,
      ]),
      initial: false,
      propertyName: "name",
      zoom: 16,
      marker: false,
      textPlaceholder: "",
    })
    .addTo(map);

  var layerControl = L.control
    .layers(
      {
        Dark: CartoDB_DarkMatter,
        Light: CartoDB_Positron,
      },
      {
        Vehicles: vehicle_layer,
        Stops: stop_layer,
        Shapes: shape_layer,
        "Parking Lots": parking_lots,
      }
    )
    .addTo(map);

  if (map.hasLayer(parking_lots) == true) {
    map.removeLayer(parking_lots);
  }

  controlSearch.on("search:locationfound", function (event) {
    event.layer.openPopup();
  });

  for (realtime of [stopsRealtime, shapesRealtime, facilitiesRealtime]) {
    realtime.on("update", function (e) {
      Object.keys(e.update).forEach(
        function (id) {
          var feature = e.update[id];
          var wasOpen = this.getLayer(id).getPopup().isOpen();
          if (wasOpen === true) {
            this.getLayer(id).closePopup();
          }

          this.getLayer(id).bindPopup(feature.properties.popupContent, {
            maxWidth: "auto",
          });

          if (wasOpen === true) {
            this.getLayer(id).openPopup();
          }
        }.bind(this)
      );
    });
  }

  vehiclesRealtime.on("update", function (e) {
    Object.keys(e.update).forEach(
      function (id) {
        var layer = this.getLayer(id);
        var feature = e.update[id];
        var wasOpen = layer.getPopup().isOpen();
        layer.unbindPopup();
        if (wasOpen === true) {
          layer.closePopup();
        }
        layer.bindPopup(feature.properties.popupContent, { maxWidth: "auto" });
        layer.setIcon(
          L.divIcon({
            html: feature.properties.icon,
            iconSize: [15, 15],
          })
        );
        if (wasOpen === true) {
          layer.openPopup();
        }
      }.bind(this)
    );
  });
  // showPredictionPopup();

  map.on("zoomend", function () {
    if (map.getZoom() < 16) {
      map.removeLayer(parking_lots);
    }
    if (map.getZoom() >= 16) {
      map.addLayer(parking_lots);
    }
    console.log(map.getZoom());
  });

  return map;
}

function plotVehicles(url, layer) {
  return L.realtime(url, {
    // interval: !["BUS", "ALL_ROUTES"].includes(ROUTE_TYPE) ? 15000 : 45000,
    interval: 15000,
    type: "FeatureCollection",
    container: layer,
    cache: false,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      var icon = L.divIcon({
        html: f.properties.icon,
        iconSize: [15, 15],
      });
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(icon);
      l.setZIndexOffset(100);
    },
  });
}

function plotStops(url, layer) {
  const stopIcon = L.icon({
    iconUrl: "static/img/mbta.png",
    iconSize: [15, 15],
  });

  return L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      // l.setStyle({ renderer: L.canvas({ padding: 0.5, tolerance: 10 }) });
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });
}

function plotShapes(url, layer) {
  let polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });

  return L.realtime(url, {
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
        color: f.properties.color,
        opacity: f.properties.opacity,
        weight: 1.3,
        renderer: polyLineRender,
      });

      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
    },
  });
}

function plotFacilities(url, layer) {
  const facilityIcon = L.icon({
    iconUrl: "static/img/parking.png",
    iconSize: [15, 15],
  });

  return L.realtime(url, {
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
}

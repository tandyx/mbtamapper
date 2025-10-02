/**
 * @file this file contains the LayerFinder class
 * @typedef {import("../utils")}
 * @exports { LayerFinder }
 * @import {strftime} from "strftime";
 * @import { Realtime, RealtimeUpdateEvent } from "leaflet";
 * @import { FetchCacheOptions } from "./types";
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("leaflet.markercluster.freezable/dist/leaflet.markercluster.freezable-src")}
 * @exports *
 */

/**
 * class that interacts with a leaflet map and provides methods to action upon specific layers
 */
class LayerFinder {
  /**
   * return a new instance from controlSearch rather than layers
   * @param {L.Map} map
   * @param {L.Control.Search} controlSearch
   * @returns {LayerFinder}
   */
  static fromControlSearch(map, controlSearch) {
    return new this(
      map,
      Object.values(controlSearch.options.layer.getLayers()).flatMap((l) =>
        l.getLayers()
      )
    );
  }

  /**
   * create a new layer finder lazily (through globals)
   * @returns {LayerFinder}
   */
  static fromGlobals() {
    return this.fromControlSearch(_map, _controlSearch);
  }

  /**
   *
   * @param {L.Map} map
   * @param {Layer[]?} layers
   */
  constructor(map, layers) {
    this.map = map;
    this.layers = layers || map._layers;
    /** @type {(L.MarkerClusterGroup)[]} */
    this.markerClusters = Object.values(this.map._layers).filter((a) =>
      Boolean(a._markerCluster)
    );
  }

  /**
   * finds layer based on predicate and options
   * @typedef {{click?: boolean, autoZoom?: boolean, zoom?: number, latLng?: L.LatLng}} FindLayerOptions
   * @param {(value: L.LayerGroup<L.GeoJSON<LayerProperty>>, index: number, array: any[]) => L.Layer?} fn
   * @param {FindLayerOptions} options
   * @returns {L.Layer?}
   */
  findLayer(fn, options = {}) {
    options = { click: true, autoZoom: true, ...options };
    const _zoom = this.map.getZoom();
    const _coords = this.map.getCenter();
    this.map.setZoom(this.map.options.minZoom, {
      animate: false,
    });
    /**@type {L.Marker?} */
    const layer = this.layers.find(fn);

    if (!layer) {
      console.error(`layer not found`);
      this.map.setView(_coords, _zoom, { animate: false });
      return;
    }

    this.markerClusters.forEach((mc) => mc.disableClustering());

    if (this.map.options.maxZoom && options.autoZoom) {
      this.markerClusters.forEach((mc) => mc.disableClustering());

      this.map.setView(
        options.latLng ?? layer.getLatLng(),
        options.zoom ?? this.map.options.maxZoom
      );
    }

    if (options.click) {
      layer.fire("click");
      this.markerClusters.forEach((mc) => mc.enableClustering());
    }
    this.markerClusters.forEach((mc) => mc.enableClustering());
    return layer;
  }

  /**
   * fires click event and zooms in on stop
   * @param {string} stopId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} stop
   */
  clickStop(stopId, options = {}) {
    return this.findLayer(
      (e) =>
        e?.feature?.properties?.child_stops
          ?.map((c) => c.stop_id)
          ?.includes(stopId) || e?.feature?.id === stopId,
      { zoom: 14, ...options }
    );
  }

  /**
   * fires click event and zooms in on route
   * @param {string} routeId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} shape
   */
  clickRoute(routeId, options = {}) {
    return this.findLayer((e) => e?.feature?.properties?.route_id === routeId, {
      zoom: this.map.options.minZoom + 2,
      latLng: this.map.getCenter(),
      ...options,
    });
  }

  /**
   * alias for clickRoute
   * @param {string} routeId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} shape
   */
  clickShape(shapeId, options = {}) {
    return this.clickRoute(shapeId, options);
  }

  /**
   * fires click event and zooms in on vehicle
   * wrapper for `findLayer`
   * @param {string} vehicleId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} vehicle
   */
  clickVehicle(vehicleId, options = {}) {
    return this.findLayer(
      (e) => e?.feature?.properties?.vehicle_id === vehicleId,
      { zoom: 14, ...options }
    );
  }
}

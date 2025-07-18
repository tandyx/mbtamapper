import L from "leaflet";
import "leaflet-sidebar";
import * as util from "../utils.js";

export type LeafletSidebar = (ReturnType<
  typeof L.control.sidebar
> extends L.Control
  ? ReturnType<typeof L.control.sidebar>
  : never) &
  L.Evented;

export interface LayerApiRealtimeOptions {
  url: string;
  layer: L.LayerGroup;
  textboxSize: string;
  isMobile: boolean;
  sidebar: LeafletSidebar;
  routeType: string;
  map: L.Map;
  interval?: number;
}

export interface RealtimeLayerOnClickOptions<T extends LayerProperty> {
  /**
   * stops pagination for the event to other map listeners
   * @default true
   */
  stopPropagation?: boolean;

  /**
   * feature's properties
   */
  properties: T;

  /**
   * because javascript is an AMAZING language
   * @default this
   */
  _this?: this;

  /**
   * id field, sets window hash, can be ignored by passing null
   * @default "id"
   */
  idField?: keyof T | "id";
}

export interface FetchCacheOptions<T extends "text" | "json"> {
  /**
   * sessionStorage or localStorage or null (no cache)
   * @default sessionStorage
   */
  storage?: Storage;
  /**
   * store and fetch as text or json
   * @default json
   */
  out?: T;
  /**
   * time (ms) to cache the response
   * @default null (indefinite)
   */
  clearAfter?: number;
  /**
   * what to do on error? returns result of this function if errors
   *
   * by default returns an empty array and `console.errors`
   *
   * @default (resp: Response) => []
   */
  onError?: (resp: Response) => any;
}

export interface LayerProperty {
  [key = string]: any;
}

export interface StopProperty extends LayerProperty {
  at_street?: string;
  level_id?: string;
  location_type: string;
  municipality: string;
  on_street?: string;
  parent_station?: string;
  platform_code?: string;
  platform_name?: string;
  stop_address?: string;
  stop_code?: string;
  stop_desc?: string;
  stop_id: string;
  stop_lat?: number;
  stop_lon?: number;
  stop_name: string;
  stop_url: string;
  vehicle_type?: string;
  wheelchair_boarding: string;
  zone_id?: ZoneID;
  child_stops?: StopProperty[];
  routes: RouteProperty[];
  alerts?: AlertProperty[];
  predictions?: PredictionProperty[];
}

export enum ZoneID {
  BoatAquarium = "Boat-Aquarium",
  BoatFan = "Boat-Fan",
  BoatGeorge = "Boat-George",
  BoatHingham = "Boat-Hingham",
  BoatHull = "Boat-Hull",
  BoatLewis = "Boat-Lewis",
  BoatLogan = "Boat-Logan",
  BoatLong = "Boat-Long",
  BoatRowes = "Boat-Rowes",
  BoatZone1A = "Boat-zone-1A",
  CFZoneBuzzards = "CF-zone-buzzards",
  CFZoneHyannis = "CF-zone-hyannis",
  CRZone1 = "CR-zone-1",
  CRZone10 = "CR-zone-10",
  CRZone1A = "CR-zone-1A",
  CRZone2 = "CR-zone-2",
  CRZone3 = "CR-zone-3",
  CRZone4 = "CR-zone-4",
  CRZone5 = "CR-zone-5",
  CRZone6 = "CR-zone-6",
  CRZone7 = "CR-zone-7",
  CRZone8 = "CR-zone-8",
  CRZone9 = "CR-zone-9",
  ExpressBusDowntown = "ExpressBus-Downtown",
  LocalBus = "LocalBus",
  RapidTransit = "RapidTransit",
  SL1Logan = "SL1-Logan",
  SLWaterfrontNonLogan = "SLWaterfrontNonLogan",
}

export interface ShapeProperty extends LayerProperty {
  shape_id: string;
  route_short_name?: string;
  route_fare_class: string;
  route_long_name: string;
  line_id: string;
  route_desc: string;
  listed_route?: boolean;
  route_type: string;
  network_id: string;
  route_url: string;
  route_color: RouteColor;
  agency_id: string;
  route_text_color: "FFFFFF";
  route_id: string;
  route_sort_order: number;
  route_name: string;
  agency: AgencyProperty;
}

export interface AgencyProperty extends LayerProperty {
  agency_timezone: "America/New_York";
  agency_lang: "EN";
  agency_id: string;
  agency_name: "MBTA" | string;
  agency_url: string;
  agency_phone: "617-222-3200" | string;
}

export interface Facility extends LayerProperty {
  capacity?: string;
  enclosed: string;
  facility_class: number;
  facility_code: null;
  facility_desc: null;
  facility_id: string;
  facility_lat: number | null;
  facility_lon: number | null;
  facility_long_name: string;
  facility_short_name: string;
  facility_type: "bike-storage";
  secured?: string;
  stop_id: string;
  wheelchair_facility: number;
  attended?: string;
  "capacity-accessible"?: string;
  contact?: string;
  "contact-phone"?: string;
  "contact-url"?: string;
  "fee-daily"?: string;
  "fee-monthly"?: string;
  municipality?: string;
  operator?: string;
  "overnight-allowed"?: string;
  owner?: string;
  "payment-app"?: string;
  "payment-app-id"?: string;
  "payment-app-url"?: string;
  "payment-form-accepted"?: string;
  "weekday-typical-utilization"?: string;
  note?: string;
  "car-sharing"?: "Zipcar";
}

export interface VehicleProperty extends LayerProperty {
  bearing: number;
  bikes_allowed: boolean;
  current_status: "IN_TRANSIT_TO" | "INCOMING_AT" | "STOPPED_AT";
  current_stop_sequence: number;
  direction_id: number;
  display_name: Name;
  headsign: string;
  label: string;
  latitude: number;
  longitude: number;
  next_stop?: PredictionProperty;
  occupancy_percentage: null;
  occupancy_status: null;
  route: RouteProperty;
  route_color: RouteColor;
  route_id: RouteID;
  speed: number | null;
  speed_mph: number | null;
  stop_id: null | string;
  stop_time?: StopTimeProperty;
  trip_id: string;
  trip_properties: any[];
  trip_short_name: string;
  vehicle_id: string;
  trip?: TripProperty;
}

export enum Name {
  B = "B",
  BlueLine = "Blue Line",
  C = "C",
  E = "E",
  Empty = "",
  MattapanTrolley = "Mattapan Trolley",
  OrangeLine = "Orange Line",
  RedLine = "Red Line",
}

export enum RouteID {
  Blue = "Blue",
  GreenB = "Green-B",
  GreenC = "Green-C",
  GreenE = "Green-E",
  Mattapan = "Mattapan",
  Orange = "Orange",
  Red = "Red",
}

export interface RouteProperty {
  agency_id: string;
  line_id: LineID;
  listed_route: null;
  network_id: NetworkID;
  route_color: RouteColor;
  route_desc: RouteDescEnum;
  route_fare_class: RouteDescEnum;
  route_id: RouteID;
  route_long_name: RouteLongName;
  route_name: Name;
  route_short_name: Name | null;
  route_sort_order: number;
  route_text_color: RouteTextColor;
  route_type: string;
  route_url: string;

  stop_times?: StopTimeProperty[];
  alerts?: AlertProperty[];
  predictions?: PredictionProperty[];
  trips?: TripProperty[];
}

export enum LineID {
  LineBlue = "line-Blue",
  LineGreen = "line-Green",
  LineMattapan = "line-Mattapan",
  LineOrange = "line-Orange",
  LineRed = "line-Red",
}

export enum NetworkID {
  MRapidTransit = "m_rapid_transit",
  RapidTransit = "rapid_transit",
}

export enum RouteColor {
  Da291C = "DA291C",
  Ed8B00 = "ED8B00",
  The003Da5 = "003DA5",
  The00843D = "00843D",
}

export enum RouteDescEnum {
  RapidTransit = "Rapid Transit",
}

export enum RouteLongName {
  BlueLine = "Blue Line",
  GreenLineB = "Green Line B",
  GreenLineC = "Green Line C",
  GreenLineE = "Green Line E",
  MattapanTrolley = "Mattapan Trolley",
  OrangeLine = "Orange Line",
  RedLine = "Red Line",
}

export enum RouteTextColor {
  Ffffff = "FFFFFF",
}

export interface StopTimeProperty {
  arrival_time: string;
  arrival_timestamp: number;
  checkpoint_id: string;
  continuous_drop_off: null;
  continuous_pickup: null;
  departure_time: string;
  departure_timestamp: number;
  destination_label: string;
  drop_off_type: string;
  early_departure: boolean;
  flag_stop: boolean;
  pickup_type: string;
  stop_headsign: null;
  stop_id: string;
  stop_name: string;
  stop_sequence: number;
  timepoint: string;
  trip_id: string;
  trip?: TripProperty;
}

export interface TripProperty {
  active?: boolean;
  bikes_allowed: boolean;
  block_id: null;
  direction_id: number;
  route_id: string;
  route_pattern_id: string;
  service_id: string;
  shape_id: string;
  trip_headsign: string;
  trip_id: string;
  trip_route_type: null;
  trip_short_name: string;
  wheelchair_accessible: number;
}

export interface PredictionProperty {
  arrival_time: number;
  delay: null;
  departure_time: number | null;
  direction_id: number;
  headsign: string;
  index: number;
  platform_name: string;
  prediction_id: string;
  route_id: string;
  stop_id: string;
  stop_name: string;
  stop_sequence: number;
  stop_time: StopTimeProperty?;
  trip_id: string;
  vehicle_id: string;
}
export interface AlertProperty {
  active_period_end: number;
  active_period_start: number;
  agency_id: string;
  alert_id: string;
  cause: string;
  description: string;
  direction_id: null;
  effect: string;
  header: string;
  route_id: string;
  route_type: string;
  severity: "WARNING" | "SEVERE" | "INFO";
  stop_id: null;
  trip_id: string;
  url: string;
}

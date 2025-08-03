/**
 * @file utils.js - misc utility functions
 * @module utils
 * @import {strftime} from "strftime";
 * @import { Realtime, RealtimeUpdateEvent } from "leaflet";
 * @import { FetchCacheOptions } from "./types";
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("../node_modules/leaflet.markercluster.freezable/dist/leaflet.markercluster.freezable-src")}
 * @exports *
 */

"use strict";

/** Check if user is on mobile
 * @returns {boolean} - whether or not user is on mobile
 */
const mobileCheck = function () {
  let check = false;
  (function (a) {
    if (
      /(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(
        a
      ) ||
      /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(
        a.substr(0, 4)
      )
    )
      check = true;
  })(navigator.userAgent || navigator.vendor || window.opera);
  return check;
};

/*
 * Check if user is on mobile
 */
const strftimeIT = strftime.localize({
  identifier: "it-IT",
  days: [
    "domenica",
    "lunedi",
    "martedi",
    "mercoledi",
    "giovedi",
    "venerdi",
    "sabato",
  ],
  shortDays: ["dom", "lun", "mar", "mer", "gio", "ven", "sab"],
  months: [
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
  ],
  shortMonths: [
    "gen",
    "feb",
    "mar",
    "apr",
    "mag",
    "giu",
    "lug",
    "ago",
    "set",
    "ott",
    "nov",
    "dic",
  ],
  AM: "AM",
  PM: "PM",
  am: "am",
  pm: "pm",
  formats: {
    D: "%m/%d/%y",
    F: "%Y-%m-%d",
    R: "%H:%M",
    X: "%T",
    c: "%a %b %d %X %Y",
    r: "%I:%M:%S %p",
    T: "%H:%M:%S",
    v: "%e-%b-%Y",
    x: "%D",
  },
});

/** Title case a string
 * @param {string} str - string to title case
 * @param {string} split - character to split string on, default `_`
 * @returns {string} - title cased string
 */
function titleCase(str, split = "_") {
  return str
    .toLowerCase()
    .split(split)
    .map(function (word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

/** Title case a string, but only the first letter
 * @param {string} str - string to title case
 * @param {string} split - character to split string on
 * @returns {string} - title cased string
 */
function almostTitleCase(str, split = "_") {
  const _str = str.toLowerCase().split(split).join(" ");
  return _str.charAt(0).toUpperCase() + _str.slice(1);
}

/** Check if user is in iframe
 * @returns {boolean} - whether or not user is in iframe
 */
function inIframe() {
  try {
    return window.self !== window.top;
  } catch (e) {
    return true;
  }
}

/**
 * Gets a c style property from an element
 * @param {string | HTMLElement} id - The element to get the style from
 * @param {string} styleProp - The style property to get
 * @returns {string} - The value of the style property
 */
function getStyle(id, styleProp) {
  const element = typeof id === "string" ? document.getElementById(id) : id;
  if (element.style[styleProp]) return element.style[styleProp];
  if (window.getComputedStyle) {
    return document.defaultView
      .getComputedStyle(element, null)
      .getPropertyValue(styleProp);
  }
  if (element.currentStyle) return element.currentStyle[styleProp];
  return "";
}

/**
 * Truncate a string
 * @param {string} str - The string to truncate
 * @param {number} num - The number of characters to truncate the string to
 * @param {string} tail - The string to append to the end of the truncated string
 * @returns {string} - The truncated string
 */
function truncateString(str, num, tail = "...") {
  if (str.length <= num) return str;
  return str.slice(0, num) + tail;
}

/**
 * formats a timestamp to a locale string
 * @param {int} timestamp - The timestamp to format
 * @param {string} strf - The format to format the timestamp to
 * @returns {string} - The formatted timestamp
 */
function formatTimestamp(timestamp, strf = "") {
  const datetime = new Date(timestamp * 1000);
  if (strf) return strftimeIT(strf, datetime);
  return datetime.toLocaleString();
}

/**
 * Gets the style of a selector from a stylesheet
 * @param {string} style - The style to get
 * @param {string} selector - The selector to get the style from
 * @param {CSSStyleSheet} sheet - The stylesheet to get the style from
 * @returns {string} - The value of the style
 * @returns {null} - If the style was not found
 */
function getStyleRuleValue(style, selector, sheet = undefined) {
  const sheets = typeof sheet !== "undefined" ? [sheet] : document.styleSheets;
  for (const sheet of sheets) {
    if (!sheet.cssRules) continue;
    for (const rule of sheet.cssRules) {
      if (rule.selectorText?.split(",").includes(selector)) {
        return rule.style[style];
      }
    }
  }
  return null;
}

/**
 * Gets a stylesheet by name
 * @param {string} sheetName - The name of the stylesheet to get
 * @returns {CSSStyleSheet} - The stylesheet
 * @returns {null} - If the stylesheet was not found
 * @example getStylesheet("nav");
 */
function getStylesheet(sheetName) {
  for (const sheet of document.styleSheets) {
    if (sheet.href?.includes(sheetName)) {
      return sheet;
    }
  }
  return null;
}

/**
 * sets a cookie to a value
 * @param {string} name - The name of the cookie
 * @param {string} value - The value of the cookie
 * @param {number | null} exdays - The number of days until the cookie expires or null if it never expires @default null
 * @returns {void}
 * @example setCookie("username", "johan", 10);
 */

function setCookie(name, value, exdays = null) {
  if (!exdays) {
    document.cookie = `${name}=${value};path=/`;
    return;
  }
  const d = new Date();
  d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};${"expires=" + d.toUTCString()};path=/`;
}

/**
 * fetches a cookie
 * @param {string} name - the name of the cookie to fetch
 * @returns {string} - the value of the cookie
 * @example let user = getCookie("username");
 */
function getCookie(name) {
  name += "=";
  for (let cookie of decodeURIComponent(document.cookie).split(";")) {
    while (cookie.charAt(0) == " ") {
      cookie = cookie.substring(1);
    }
    if (cookie.indexOf(name) == 0) {
      return cookie.substring(name.length, cookie.length);
    }
  }
  return "";
}

/**
 * gets a default cookie value, sets the cookie if it does not exist
 * @param {string} name - the name of the cookie
 * @param {string} value - value of the cookie @default ""
 * @param {number | null} numDays - the number of days until the cookie expires or null if it never expires @default null
 * @returns {string} - the value of the cookie
 * @example let user = getDefaultCookie("username", "johan", 10);
 */
function getDefaultCookie(name, value = "", numDays = null) {
  let cookie = getCookie(name);
  if (!cookie) {
    cookie = value;
    setCookie(name, value, numDays);
  }
  return cookie;
}
/**
 *
 * @typedef {ReturnType<specialStopTimeAttrs>} StopTimeAttrObj
 *
 * for flag, early departure stops
 * @param {StopTimeProperty?} properties
 * @param {RouteProperty?} route
 */
function specialStopTimeAttrs(properties, route) {
  const objec = { cssClass: "", tooltip: "", htmlLogo: "" };
  if (!properties) return objec;

  const flag_stop =
    properties?.flag_stop ??
    ([properties.pickup_type, properties.drop_off_type].includes("3") &&
      route?.route_type == "2");

  const early_departure =
    properties?.early_departure ??
    (properties.timepoint == "0" && route?.route_type == "2");

  if (flag_stop) {
    objec.cssClass = "flag_stop";
    objec.tooltip = "Flag Stop";
    objec.htmlLogo = "<i> f</i>";
  } else if (early_departure) {
    objec.cssClass = "early_departure";
    objec.tooltip = "Early Departure";
    objec.htmlLogo = "<i> L</i>";
  }
  return objec;
}

/**
 * gets the value (style) of a css var
 * @param {string} name - the name of the css variable
 * @returns {string} the value of the css variable
 */

function getCssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name);
}

/**
 * sets the value of a css var
 * @param {string} name - the name of the css variable
 * @param {string} value - the value to set the css variable to
 * @returns {void}
 */
function setCssVar(name, value) {
  document.documentElement.style.setProperty(name, value);
}

/**
 *  Check if the device is like a mobile device
 * @returns {boolean} - whether or not the device is a mobile device
 */
function isLikeMobile(threshold = null) {
  if (threshold === null) {
    threshold = getCssVar("--mobile-threshold");
  }
  return window.innerWidth <= 768;
}

/**
 * gets delay text formatted
 * @param {int} delay
 * @param {boolean} [addMin=true] adds `" min"` to the end of the string
 * @returns {string} - the delay text
 */
function getDelayText(delay, addMin = true) {
  let delayText = delay ? `${Math.floor(delay / 60)}` : "";
  if (delayText === "0") {
    delayText = "";
  } else if (delay > 0) {
    delayText = `+${delayText}`;
  }
  if (delayText && addMin) {
    delayText += " min";
  }
  return delayText;
}

/**
 * gets the delay class name
 * @template {number} T
 * @param {T} delay - delay in seconds
 * @returns {"severe-delay" | "moderate-delay" | "slight-delay" | "on-time"} - the delay class name
 */
function getDelayClassName(delay) {
  if (delay >= 900) {
    return "severe-delay";
  }
  if (delay >= 600) {
    return "moderate-delay";
  }
  if (delay > 60) {
    return "slight-delay";
  }
  return "on-time";
}

/**
 * blends two hex colors, returning their average
 * @param {string} color1
 * @param {string} color2
 * @returns {`#${string}`}
 */
function mixHexColors(color1, color2) {
  // Remove the '#' from the hex strings if present
  color1 = color1.startsWith("#") ? color1.slice(1) : color1;
  color2 = color2.startsWith("#") ? color2.slice(1) : color2;

  // Convert hex to RGB components
  const r1 = parseInt(color1.slice(0, 2), 16);
  const g1 = parseInt(color1.slice(2, 4), 16);
  const b1 = parseInt(color1.slice(4, 6), 16);

  const r2 = parseInt(color2.slice(0, 2), 16);
  const g2 = parseInt(color2.slice(2, 4), 16);
  const b2 = parseInt(color2.slice(4, 6), 16);

  // Average the RGB components
  const rMix = Math.round((r1 + r2) / 2);
  const gMix = Math.round((g1 + g2) / 2);
  const bMix = Math.round((b1 + b2) / 2);

  // Convert back to hex and format with leading zeros if needed
  const mixedColor = `#${rMix.toString(16).padStart(2, "0")}${gMix
    .toString(16)
    .padStart(2, "0")}${bMix.toString(16).padStart(2, "0")}`;

  return mixedColor;
}
/**
 *
 * @param {number} time in seconds
 * @param {("hours" | "minutes" | "seconds")[]} ignore - array of strings to ignore
 * @returns {string} - the time in hours, minutes, and seconds
 */
function minuteify(time, ignore = []) {
  const hours = Math.floor(time / 3600);
  const minutes = Math.floor((time % 3600) / 60);
  const seconds = parseInt(time % 60);

  let result = "";
  if (hours > 0 && !ignore.includes("hours")) {
    result += `${hours} hr `;
  }
  if (minutes > 0 && !ignore.includes("minutes")) {
    result += `${minutes} min `;
  }
  if (seconds > 0 && !ignore.includes("seconds")) {
    result += `${seconds} sec`;
  }
  return result.trim();
}

/**
 * on theme change
 * @param {Theme} _theme
 * @returns
 */
function onThemeChange(_theme) {
  const cLayer = document.getElementsByClassName("leaflet-control-layers");
  if (!cLayer.length) return;
  const elements = cLayer[0].getElementsByTagName("input");
  elements[{ light: 0, dark: 1 }[_theme.theme]]?.click();
}

/**
 * only works in `await` or `.then` situations
 * @param {number} time in ms
 * @returns {Promise<any>}
 */
function sleep(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

/**
 * gets storage or default value.
 *
 * sets `_default` value into storage
 *
 * defaults to sessionStorage
 *
 * @param {string} key
 * @param {any} _default
 * @param {{storage?: Storage, parseInt?: boolean, parseFloat?: boolean, parseJson?: boolean}} options
 * @returns {any}
 */
function storageGet(key, _default, options = {}) {
  const _storage = options.storage || sessionStorage;
  const _item = _storage.getItem(key);
  if (!_item) {
    _storage.setItem(key, _default);
    return _default;
  }
  if (options.parseFloat) return parseFloat(_item);
  if (options.parseInt) return parseInt(_item);
  if (options.parseJson) return JSON.parse(_item);
  return _item;
}

/**
 *
 * cache fetch requests in local or session storage
 *
 * auto assumes json but will default to text if failed
 *
 * `out` defaults to json, `storage` defaults to sessionStorage, `clearAfter` defaults to indefinite (ms)
 *
 * @template {"json" | "text"} T
 *
 * @param {string} url
 * @param {RequestInit} fetchParams
 * @param {FetchCacheOptions<T>} options
 * @returns {Promise<FetchCacheOptions<T> extends "json" ? any : string>}
 */
async function fetchCache(url, fetchParams, options = {}) {
  const { storage = sessionStorage, out = "json", clearAfter } = options;
  const cacheData = storage?.getItem(url);
  if (cacheData && storage) {
    if (out === "text") return cacheData;
    return JSON.parse(cacheData);
  }
  const resp = await fetch(url, fetchParams);
  if (!resp.ok) {
    if (options.onError) return options.onError(resp);
    console.error(`${resp.status}: ${await resp.text()}`);
    return [];
  }
  if (!storage) {
    return out === "json" ? await resp.json() : await resp.text();
  }
  let data;
  if (out === "json") {
    data = await resp.json();
    storage.setItem(url, JSON.stringify(data));
  } else {
    data = await resp.text();
    storage.setItem(url, data);
  }
  if (clearAfter) setTimeout(() => storage.removeItem(url), clearAfter);

  return data;
}

/**
 * html element from string
 * @param {string} htmlString
 */
function createElementFromHTML(htmlString) {
  return new DOMParser().parseFromString(htmlString, "text/xml").children[0];
  // Change this to div.childNodes to support multiple top-level nodes.
}
/**
 * gets the best constrasting text color from a hex
 * @param {`${'#'}${string}` | string} hexcolor may or may not start with `#`
 * @param {number} [tresh=128] treshhold
 * @returns {"dark" | "light"}
 */
function getContrastYIQ(hexcolor, tresh = 128) {
  while (hexcolor.charAt(0) === "#") {
    hexcolor = hexcolor.substring(1);
  }
  var r = parseInt(hexcolor.substring(1, 3), 16);
  var g = parseInt(hexcolor.substring(3, 5), 16);
  var b = parseInt(hexcolor.substring(5, 7), 16);
  var yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= tresh ? "dark" : "light";
}

/**
 * class for theme management
 * @template {"dark" | "light"} T
 */
class Theme {
  /**
   * where the theme key is stored
   */
  static THEME_STORAGE_KEY = "_theme";

  /**
   * gets the system theme through window.watchMedia
   * @returns {"dark" | "light" | null}
   */
  static get systemTheme() {
    for (const scheme of ["dark", "light"]) {
      if (window.matchMedia(`(prefers-color-scheme: ${scheme})`).matches) {
        return scheme;
      }
    }
    // if (window.matchMedia(`(prefers-color-scheme: dark)`).matches) {
    //   return "dark";
    // }
    // return "light";
  }
  /**
   * gets the active theme from either the html element or system theme
   * @returns {"dark" | "light"}
   */
  static get activeTheme() {
    return document.documentElement.dataset.mode || this.systemTheme;
  }

  /**
   * returns unicode icon from sys active theme
   */
  static get unicodeIcon() {
    return this.activeTheme === "dark" ? "\uf186" : "\uf185";
  }

  /**
   * returns unicode icon from sys active theme
   */
  get unicodeIcon() {
    return this.theme === "dark" ? "\uf186" : "\uf185";
  }

  /**
   * factory; creates new `Theme` from existing settings
   * @param {Storage?} [storagePriorty=null] pointer to first storage to use default sessionStorage before local.
   */
  static fromExisting(storagePriorty = null) {
    const pStore = storagePriorty || sessionStorage || localStorage;
    const secStore = pStore === sessionStorage ? localStorage : sessionStorage;
    return new this(
      document.documentElement.dataset.mode ||
        pStore.getItem(this.THEME_STORAGE_KEY) ||
        secStore?.getItem(this.THEME_STORAGE_KEY) ||
        this.systemTheme ||
        "light"
    );
  }
  /**
   * manually create a new theme object.
   * @param {T} theme "dark" or "light"; will throw error if not
   */
  constructor(theme) {
    if (!["light", "dark"].includes(theme)) throw new Error("only light||dark");
    this.theme = theme;
  }

  /**
   * opposite theme object without setting
   * @typedef {T extends "dark" ? Theme<"light"> : Theme<"dark">} OppTheme
   * @returns {OppTheme}
   */
  get opposite() {
    return new Theme(this.theme === "dark" ? "light" : "dark");
  }

  /**
   * sets <html data-mode="this.theme"> and saves it to session storage
   * @param {Storage?} storage storage to save to, default doesn't save
   * @param {((theme: this) => null)?} onSave callback that executes after save.
   * @returns {this}
   */
  set(storage = null, onSave = null) {
    document.documentElement.setAttribute("data-mode", this.theme);
    if (storage) storage.setItem(Theme.THEME_STORAGE_KEY, this.theme);
    if (onSave) onSave(this);
    return this;
  }
  /**
   * reverses the theme (if dark -> light)
   * this is the same as new `Theme().opposite.set()`
   * @param {Storage?} storage storage to save to, default doesn't save
   * @param {((theme: OppTheme) => null)?} onSave executed callback function when changing; `theme` is the NEW theme
   * @returns {OppTheme}
   * @example
   * const theme = Theme.fromExisting().reverse()
   */
  reverse(storage = null, onSave = null) {
    return this.opposite.set(storage, onSave);
  }
}
/**
 * memory storage class
 *
 * basically just a wrapper for Map, but with the same methods as builtin `Storage`
 *
 * @template {Map<keyof, string>} M
 */
class MemoryStorage {
  /**
   * @param {M} map - the map to use as storage
   */
  constructor(map = new Map()) {
    this.store = map;
  }

  /**
   * length of the store
   */
  get length() {
    return this.store.size;
  }

  /**
   * gets the key at the index
   * @param {number} index
   * @returns
   */
  key(index) {
    return Array.from(this.store.keys())[index] || null;
  }
  /**
   *
   * @param {keyof M} key
   * @returns
   */
  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }

  /**
   * sets the item in the store
   * @param {keyof M | keyof} key
   * @param {any} value (cast to string)
   */
  setItem(key, value) {
    this.store.set(key, `${value}`);
  }

  /**
   * removes the item from the store
   * @param {keyof M} key
   */
  removeItem(key) {
    this.store.delete(key);
  }

  /**
   * clears the store
   */
  clear() {
    this.store.clear();
  }
}

const memStorage = new MemoryStorage();
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
    console.log(options.zoom ?? this.map.options.maxZoom);
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
      zoom: this.map.options.minZoom,
      latLng: this.map.getCenter(),
      ...options,
    });
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

/** Get base layer dictionary
 * @summary Get base layer dictionary
 * @param {string} lightId - id of light layer
 * @param {string} darkId - id of dark layer
 * @param {object} additionalLayers - additional layers to add to dictionary
 * @returns {{ light: TileLayer.Provider; dark: TileLayer.Provider}} - base layer dictionary
 */
function getBaseLayerDict(
  lightId = "CartoDB.Positron",
  darkId = "CartoDB.DarkMatter",
  additionalLayers = {}
) {
  const options = {
    attribution:
      "<a href='https://www.openstreetmap.org/copyright' target='_blank' rel='noopener'>open street map</a> @ <a href='https://carto.com/attribution' target='_blank' rel='noopener'>carto</a>",
  };
  const baseLayers = {
    light: L.tileLayer.provider(lightId, { id: "lightLayer", ...options }),
    dark: L.tileLayer.provider(darkId, { id: "darkLayer", ...options }),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}

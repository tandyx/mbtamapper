/**
 * @file utils.js - misc utility functions
 * @module utils
 * @import {strftime} from "strftime";
 * @import { Realtime } from "leaflet";
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

/** Handle update event for realtime layers
 * @param {Realtime} entity - realtime layer to update
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
/**@type {string[]} */
const openPopups = [];
/**
 * Toggles a popup
 * @param {string | HTMLElement} id - the id of the popup or the popup element
 * @param {boolean | "auto"} show - whether or not to show the popup
 * @returns {void}
 */
function togglePopup(id, show = "auto") {
  const popup = typeof id === "string" ? document.getElementById(id) : id;
  // console.log(popup);
  if (!popup) return;
  const identifier = popup.id || popup.name;
  if (!popup.classList.contains("show")) {
    openPopups.push(identifier);
  } else {
    openPopups.splice(openPopups.indexOf(identifier), 1);
  }
  if (show === "auto") {
    popup.classList.toggle("show");
    return;
  }
  if (show) {
    popup.classList.add("show");
    if (!popup.classList.contains("show")) openPopups.push(identifier);
    return;
  }
  popup.classList.remove("show");
  openPopups.splice(openPopups.indexOf(identifier), 1);
}

/**
 * gets delay text formatted
 * @param {int} delay
 * @returns {string} - the delay text
 */
function getDelayText(delay) {
  let delayText = delay ? `${Math.floor(delay / 60)}` : "";
  if (delayText === "0") {
    delayText = "";
  } else if (delay > 0) {
    delayText = `+${delayText}`;
  }
  if (delayText) {
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

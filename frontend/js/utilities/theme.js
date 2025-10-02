/**
 * @file this file contains the theme class
 * @typedef {import("../utils")}
 * @exports { Theme }
 * @import {strftime} from "strftime";
 * @import { Realtime, RealtimeUpdateEvent } from "leaflet";
 * @import { FetchCacheOptions } from "./types";
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("../node_modules/leaflet.markercluster.freezable/dist/leaflet.markercluster.freezable-src")}
 * @exports *
 */

"use strict";

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
    const pStore = storagePriorty || localStorage || sessionStorage;
    const secStore =
      JSON.stringify(pStore) === JSON.stringify(sessionStorage)
        ? localStorage
        : sessionStorage;
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
    theme = theme.toLowerCase();
    if (!["light", "dark"].includes(theme)) {
      throw new Error("only 'light' or 'dark' allowed");
    }
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

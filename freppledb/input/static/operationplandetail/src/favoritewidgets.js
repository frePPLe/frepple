/*
 * Copyright (C) 2026 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 */

/*
 * Widget layout, kanban columns, grouping and the active filter are saved
 * as part of a favorite, without modifying freppledb/common/static/js/frepple.js.
 *
 * Wrapping `grid.getGridConfig` lets the stock `favorite.save` pick them up
 * automatically. Wrapping `favorite.open` gates the restore on unsaved edits
 * (through the shared `attemptModeChange` flow) and notifies the state
 * owners through custom events carrying the favorite object by reference:
 * - `favorite-apply` (before the stock grid restore): the Vue bridge
 *   (useLegacyBridge.js) or this report's AngularJS template applies
 *   widgets + columns + grouping + filter to the store/globals.
 * - `favorite-opened` (after the stock grid restore): the AngularJS
 *   template re-fetches calendar/kanban/gantt data; a deferred
 *   saveColumnConfiguration persists the restored widget layout.
 * The stock grid restore itself always runs and owns the whole jqGrid side
 * (columns, widths, frozen columns, filter, pills, sorting, reload).
 *
 * Plain ES5, no modules: this file is concatenated and minified by the
 * grunt `minify` task and loaded directly by the operationplan templates.
 * Loading it installs the wrappers (with retries while legacy scripts are
 * still loading).
 */
(function () {
  'use strict';

  var DETAIL_KEYS = ['widgets', 'columns', 'grouping', 'groupingdir', 'filter'];

  function getWindow() {
    return typeof window !== 'undefined' ? window : {};
  }

  function warn() {
    if (typeof console !== 'undefined' && typeof console.warn === 'function') {
      console.warn.apply(console, arguments);
    }
  }

  function readExtraPreference(w) {
    try {
      var fn = w.extraPreference;
      if (typeof fn === 'function') return fn() || {};
    } catch (err) {
      warn('Failed to read extraPreference for favorite', err);
    }
    return {};
  }

  function hasWidgetNodes() {
    try {
      if (typeof document === 'undefined') return true;
      return document.querySelectorAll('.widget').length > 0;
    } catch (err) {
      warn('Failed to check for widget nodes', err);
      return true;
    }
  }

  function readWidgetConfig(w) {
    try {
      if (w.widget && typeof w.widget.getConfig === 'function') {
        if (!hasWidgetNodes()) return undefined;
        return w.widget.getConfig();
      }
    } catch (err) {
      warn('Failed to read widget config for favorite', err);
    }
    return undefined;
  }

  function readCurrentFilter(w) {
    // In table mode jqGrid postData is authoritative (read by the stock
    // getGridConfig). In kanban/gantt/calendar the grid is hidden and stale,
    // so read the live filter from the template globals instead.
    try {
      var f = w.thefilter || w.initialfilter;
      if (!f) return undefined;
      return typeof f === 'string' ? f : JSON.stringify(f);
    } catch (err) {
      warn('Failed to read current filter for favorite', err);
    }
    return undefined;
  }

  function hasUnsavedChanges(w) {
    try {
      var pending = w.operationplanChanges;
      if (pending && typeof pending === 'object' && Object.keys(pending).length > 0) return true;
    } catch (err) {
      warn('Failed to check for unsaved changes', err);
    }
    return false;
  }

  function getFavoriteName(event) {
    try {
      var target = event ? event.target : null;
      var anchor = target && typeof target.closest === 'function'
        ? target.closest('a.dropdown-item')
        : null;
      if (anchor) {
        var nodes = anchor.childNodes || [];
        var name = '';
        for (var i = 0; i < nodes.length; i++) {
          if (nodes[i].nodeType === 3) {
            name = nodes[i].textContent || '';
            break;
          }
        }
        if (!name) name = anchor.textContent || '';
        if (name && name.trim()) return name.trim();
      }
    } catch (err) {
      warn('Failed to parse favorite name', err);
    }
    return (event && event.detail && event.detail.name) || '';
  }

  function dispatchTarget() {
    if (typeof document === 'undefined') return null;
    return document.getElementById('app') || document;
  }

  function installFavoriteWidgetsPatch() {
    var w = getWindow();
    if (!w || w.__favoriteWidgetsPatched) return false;
    if (!w.favorite || !w.grid || typeof w.grid.getGridConfig !== 'function') return false;

    var origGetGridConfig = w.grid.getGridConfig.bind(w.grid);
    w.grid.getGridConfig = function () {
      var cfg = origGetGridConfig();
      try {
        var extra = readExtraPreference(w);
        for (var i = 0; i < DETAIL_KEYS.length; i++) {
          var k = DETAIL_KEYS[i];
          if (extra[k] !== undefined) cfg[k] = extra[k];
        }
        if (cfg.widgets === undefined) {
          var widgets = readWidgetConfig(w);
          if (widgets !== undefined) cfg.widgets = widgets;
        }
        if (!cfg.filter) {
          var filter = readCurrentFilter(w);
          if (filter !== undefined) cfg.filter = filter;
        }
      } catch (err) {
        warn('Failed to extend grid config with widgets for favorite', err);
      }
      return cfg;
    };

    var origOpen = w.favorite.open.bind(w.favorite);
    w.favorite.open = function (event) {
      var favName = getFavoriteName(event);
      var fav = favName && w.favorites ? w.favorites[favName] : undefined;
      if (!fav) return origOpen(event);
      var hasWidgets = !!fav.widgets;

      var doOpen = function () {
        // Let the state owner (Vue bridge or AngularJS template) apply
        // widgets + columns + grouping + filter BEFORE the stock restore,
        // so the saveColumnConfiguration() inside the stock open (via
        // extraPreference -> collect-preferences) already sees the restored
        // layout instead of stale state.
        try {
          var target = dispatchTarget();
          if (target) {
            target.dispatchEvent(
              new CustomEvent('favorite-apply', {
                detail: { name: favName, fav: fav, widgets: fav.widgets },
              })
            );
          }
        } catch (err) {
          warn('Failed to dispatch favorite-apply event', err);
        }

        // The stock open parses the stored filter unguarded; a corrupt
        // value would throw mid-restore. Neutralize it for this open only
        // (the stored favorite is restored afterwards) so the grid simply
        // ends up unfiltered instead of half-restored.
        var guarded = false;
        var storedFilter;
        try {
          if (
            'filter' in fav &&
            typeof fav.filter === 'string' &&
            fav.filter
          ) {
            JSON.parse(fav.filter);
          }
        } catch (parseErr) {
          warn('Failed to parse favorite filter, opening unfiltered', parseErr);
          storedFilter = fav.filter;
          fav.filter = '';
          guarded = true;
        }
        var ret;
        try {
          ret = origOpen(event);
        } finally {
          if (guarded) {
            try {
              fav.filter = storedFilter;
            } catch (restoreErr) {
              warn('Failed to restore favorite filter after opening', restoreErr);
            }
          }
        }

        // Post-open notification: AngularJS re-fetches calendar/kanban/gantt
        // data with the restored filter.
        try {
          var openedTarget = dispatchTarget();
          if (openedTarget) {
            openedTarget.dispatchEvent(
              new CustomEvent('favorite-opened', { detail: { name: favName, fav: fav } })
            );
          }
        } catch (err) {
          warn('Failed to dispatch favorite-opened event', err);
        }

        if (hasWidgets) {
          // Defer a second save so the UI can re-render the restored widget
          // order first; otherwise a save would read the stale DOM order.
          setTimeout(function () {
            try {
              w.grid.saveColumnConfiguration();
            } catch (err) {
              warn('Failed to save restored widget layout', err);
            }
          }, 250);
        }
        return ret;
      };

      // Like mode switches: with unsaved edits, defer the whole restore
      // through the shared attemptModeChange / unsavedChangesModal flow.
      try {
        var appEl = typeof document !== 'undefined' ? document.getElementById('app') : null;
        if (appEl && hasUnsavedChanges(w)) {
          appEl.dispatchEvent(
            new CustomEvent('attemptModeChange', {
              detail: {
                mode: w.mode,
                modeChangeFunction: doOpen,
              },
            })
          );
          return;
        }
      } catch (err) {
        warn('Failed to gate favorite open on unsaved changes', err);
      }
      return doOpen();
    };

    w.__favoriteWidgetsPatched = true;
    return true;
  }

  // Legacy scripts (favorite/grid) may load after this file, so retry with
  // backoff instead of once, with a final attempt on window load.
  function ensureInstalled(maxAttempts, delayMs) {
    maxAttempts = maxAttempts || 10;
    delayMs = delayMs || 500;
    var attempts = 0;
    var loadHooked = false;
    var tryInstall = function () {
      attempts++;
      try {
        if (installFavoriteWidgetsPatch()) return;
      } catch (err) {
        warn('Failed to install favorite widgets patch', err);
      }
      if (attempts < maxAttempts) {
        setTimeout(tryInstall, delayMs);
      } else if (typeof window !== 'undefined' && !loadHooked) {
        loadHooked = true;
        if (document.readyState === 'complete') {
          warn('Favorite widgets patch could not be installed: window.favorite/grid missing');
        } else {
          window.addEventListener('load', function onLoad() {
            window.removeEventListener('load', onLoad);
            try {
              if (!installFavoriteWidgetsPatch()) {
                warn('Favorite widgets patch could not be installed: window.favorite/grid missing');
              }
            } catch (err) {
              warn('Failed to install favorite widgets patch on load', err);
            }
          });
        }
      }
    };
    tryInstall();
  }

  if (!installFavoriteWidgetsPatch()) {
    ensureInstalled(10, 500);
  }
})();

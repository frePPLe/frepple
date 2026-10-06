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
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

/*
 * Owns the favorites map of the current report: named snapshots of a report
 * configuration, stored server side under the document's `favorites` key.
 *
 * Like the preference service, this exposes no API: callers talk to it with
 * CustomEvents on `document`. Dispatch is synchronous, so a caller reads its
 * answer straight off the detail object it passed in.
 *
 *   favorites:get     in   {name}           answer: detail.value
 *   favorites:names   in   {}               answer: detail.value
 *   favorites:set     in   {name, config}
 *   favorites:remove  in   {name}
 *
 * Writes are persisted by the preference service. This dispatches
 * `preferences:set` with the favorites patch and lets that service post the
 * document, so there is a single writer for changes the app initiates instead
 * of two debounced whole-document posts racing. The preference service
 * therefore has to be loaded alongside this one - the report template loads
 * both, preference service first.
 *
 * frepple.js keeps its own star dropdown and favorite.save/remove, untouched.
 * Both write the same map, which is what keeps them in agreement.
 */
window.FavoritesService = (function (w) {
  'use strict';

  /*
   * The published map, with a null prototype.
   *
   * The null prototype is what lets a favorite be named "constructor" or
   * "toString": frepple.js resolves favorites with the `in` operator
   * (favorite.check, favorite.open), which would otherwise find those on
   * Object.prototype and refuse the save, or throw on open.
   *
   * The document is pointed at this same object rather than a copy of it.
   * Django publishes `window.favorites` and `window.preferences` as two
   * independent `|json` renderings of one map (admin/base_site_grid.html), and
   * the preference service posts the whole document, so left as two copies a
   * preference write would drop a favorite stored here. Sharing one object
   * means neither can clobber the other.
   */
  function map() {
    var current = w.favorites;
    if (!current || typeof current !== 'object' || Object.getPrototypeOf(current) !== null) {
      current = Object.assign(Object.create(null), current || {});
      w.favorites = current;
    }
    if (w.preferences && w.preferences.favorites !== current) {
      w.preferences.favorites = current;
    }
    return current;
  }

  /*
   * Persisting is the preference service's job: it owns the document and posts
   * it. Handing it a favorites patch keeps one writer for changes the app
   * initiates, so a favorite set alongside a preference rides in the same POST
   * instead of the two racing.
   */
  function persist() {
    document.dispatchEvent(
      new CustomEvent('preferences:set', { detail: { patch: { favorites: map() } } })
    );
  }

  function names() {
    return Object.keys(map()).sort();
  }

  function has(name) {
    return typeof name === 'string' && Object.prototype.hasOwnProperty.call(map(), name);
  }

  /*
   * Rebuild the star dropdown from the map.
   *
   * frepple.js maintains its own <li> inside favorite.save and favorite.remove,
   * which the Vue app cannot reach: save reads the name out of #favoritename,
   * and remove asks for confirmation. Rebuilding from the map rather than
   * replicating that insertion cannot drift out of step with it, and covers a
   * removal for free.
   */
  function renderDropdown() {
    var list = $('#favoritelist');
    if (!list.length) return;
    /* Drop the entries whose link opens a favorite; the save row stays. */
    list.find('a.dropdown-item[onclick*="favorite.open"]').closest('li').remove();
    list.find('li.divider').remove();

    var favorites = names();
    if (favorites.length) {
      /* Nodes, not markup: a favorite name is user input. */
      var entries = favorites.map(function (name) {
        var link = $('<a class="dropdown-item"></a>')
          .attr('href', '#')
          .attr('onclick', 'event.stopPropagation(); favorite.open(event)')
          .text(name);
        link.append(
          $('<div style="float:right"></div>').append(
            $('<span class="fa fa-trash-o"></span>').attr('onclick', 'favorite.remove(event)')
          )
        );
        return $('<li></li>').append(link);
      });
      list.children('li').last().before(entries);
    }

    /* Keep the Save button's enabled state in step with what exists now. This
     * has to run on the way out of an empty map too, or removing the last
     * favorite leaves a disabled Save button behind a name that is now free. */
    if (w.favorite && typeof w.favorite.check === 'function') w.favorite.check();
  }

  document.addEventListener('favorites:get', function (e) {
    if (e.detail) e.detail.value = has(e.detail.name) ? map()[e.detail.name] : undefined;
  });

  document.addEventListener('favorites:names', function (e) {
    if (e.detail) e.detail.value = names();
  });

  document.addEventListener('favorites:set', function (e) {
    if (!e.detail || !e.detail.config) return;
    var name = e.detail.name;
    if (typeof name !== 'string' || name.length === 0) return;
    map()[name] = e.detail.config;
    persist();
    renderDropdown();
  });

  document.addEventListener('favorites:remove', function (e) {
    if (!e.detail || !has(e.detail.name)) return;
    delete map()[e.detail.name];
    persist();
    renderDropdown();
  });

  /* Seed the prototype and share the copies on load, so a favorite can be
   * stored under an Object.prototype name before any Vue code runs. */
  map();

  return {};
})(window);

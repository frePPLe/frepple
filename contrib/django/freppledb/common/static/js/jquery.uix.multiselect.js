/*
 * jQuery UIx Multiselect 2.0
 *
 * Authors:
 *  Yanick Rochon (yanick.rochon[at]gmail[dot]com)
 *
 * Licensed under the MIT (MIT-LICENSE.txt) license.
 *
 * http://mind2soft.com/labs/jquery/multiselect/
 *
 *
 * Depends:
 * jQuery UI 1.8+
 *
 */

;(function($, window, undefined) {
    // ECMAScript 5 Strict Mode: [John Resig Blog Post](http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/)
    "use strict";

    // Each instance must have their own drag and drop scope. We use a global page scope counter
    // so we do not create two instances with mistankenly the same scope! We do not support
    // cross instance drag and drop; this would require also copying the OPTION element and it
    // would slow the component down. This is not the widget's contract anyhow.
    var globalScope = 0;

    var DEF_OPTGROUP = '';
    var PRE_OPTGROUP = 'group-';

    // these events will trigger on the original element
    //var NATIVE_EVENTS = ["change"];   // for version 2.1

    // a list of predefined events
    //var EVENT_CHANGE = 'change';    // for version 2.1
    var EVENT_CHANGE = 'multiselectChange';
    //var EVENT_SEARCH = 'beforesearch';   // for version 2.1
    var EVENT_SEARCH = 'multiselectSearch';

    // The jQuery.uix namespace will automatically be created if it doesn't exist
    $.widget("uix.multiselect", {
        options: {
            availableListPosition: 'right',// 'top', 'right', 'bottom', 'left'; the position of the available list (default: 'right')
            // beforesearch: null,            // a funciton called before searching. If the default is prevented, search will not happen (for version 2.1)
            collapsableGroups: true,       // tells whether the option groups can be collapsed or not (default: true)
            created: null,                 // a function called when the widget is done loading (default: null)
            defaultGroupName: '',          // the name of the default option group (default: '')
            filterSelected: false,         // when searching, filter selected options also? (default: false)
            locale: 'auto',                // any valid locale, 'auto', or '' for default built-in strings (default: 'auto')
            moveEffect: null,              // 'blind','bounce','clip','drop','explode','fold','highlight','puff','pulsate','shake','slide' (default: null)
            moveEffectOptions: {},         // effect options (see jQuery UI documentation) (default: {})
            moveEffectSpeed: null,         // string ('slow','fast') or number in millisecond (ignored if moveEffect is 'show') (default: null)
            optionRenderer: false,         // a function that will return the item element to be rendered in the list (default: false)
            optionGroupRenderer: false,    // a function that will return the group item element to be rendered (default: false)
            searchField: 'toggle',         // false, true, 'toggle'; set the search field behaviour (default: 'toggle')
            searchFilter: null,            // a search filter. Will receive the OPTION element and should return a boolean value.
            searchHeader: 'available',     // 'available', 'selected'; set the list header that will host the search field (default: 'available')
            selectionMode: 'click,d&d',    // how options can be selected separated by commas: 'click', "dblclick" and 'd&d' (default: 'click,d&d')
            showDefaultGroupHeader: false, // show the default option group header (default: false)
            showEmptyGroups: false,        // always display option groups even if empty (default: false)
            splitRatio: 0.55,              // % of the left list's width of the widget total width (default 0.55)
            sortable: false,               // if the selected list should be user sortable or not
            sortMethod: null               // null, 'standard', 'natural'; a sort function name (see ItemComparators), or a custom function (default: null)
        },

        _create: function() {
            var that = this;
            var selListHeader, selListContent, avListHeader, avListContent;
            var btnSelectAll, btnDeselectAll;

            this.scope = 'multiselect' + (globalScope++);
            this.optionGroupIndex = 1;
            this._setLocale(this.options.locale);

            this.element.addClass('uix-multiselect-original');
            this._elementWrapper = $('<div></div>').addClass('uix-multiselect ui-widget')
                .css({
                    'width': this.element.outerWidth(),
                    'height': this.element.outerHeight()
                })
                .append(
                    $('<div></div>').addClass('multiselect-selected-list')
                        .append( $('<div></div>').addClass('ui-widget-header')
                            .append( btnDeselectAll = $('<button></button>', { type:"button" }).addClass('uix-control-right')
                                .attr('data-localekey', 'deselectAll')
                                .attr('title', this._t('deselectAll'))
                                .button({icons:{primary:'ui-icon-arrowthickstop-1-e'}, text:false})
                                .click(function(e) { e.preventDefault(); e.stopPropagation(); that.optionCache.setSelectedAll(false); return false; })
                            )
                            .append( selListHeader = $('<div></div>').addClass('header-text') )
                        )
                        .append( selListContent = $('<div></div>').addClass('uix-list-container ui-widget-content') )
                )
                ['right,top'.indexOf(this.options.availableListPosition)>=0?'prepend':'append'](
                    $('<div></div>').addClass('multiselect-available-list')
                        .append( $('<div></div>').addClass('ui-widget-header')
                            .append( btnSelectAll = $('<button></button>', { type:"button" }).addClass('uix-control-right')
                                .attr('data-localekey', 'selectAll')
                                .attr('title', this._t('selectAll'))
                                .button({icons:{primary:'ui-icon-arrowthickstop-1-w'}, text:false})
                                .click(function(e) { e.preventDefault(); e.stopPropagation(); that.optionCache.setSelectedAll(true); return false; })
                            )
                            .append( avListHeader = $('<div></div>').addClass('header-text') )

                        )
                        .append( avListContent  = $('<div></div>').addClass('uix-list-container ui-widget-content') )
                )
                .insertAfter(this.element)
            ;

            this._buttons = {
                'selectAll': btnSelectAll,
                'deselectAll': btnDeselectAll
            };
            this._headers = {
                'selected': selListHeader,
                'available': avListHeader
            };
            this._lists = {
                'selected': selListContent.attr('id', this.scope+'_selListContent'),
                'available': avListContent.attr('id', this.scope+'_avListContent')
            };

            this.optionCache = new OptionCache(this);
            this._searchDelayed = new SearchDelayed(this, {delay: 500});

            this._initSearchable();

            this._applyListDroppable();

            this.refresh(this.options.created);
        },

        /**
         * ***************************************
         *   PUBLIC
         * ***************************************
         */

        /**
         * Refresh all the lists from the underlaying element. This method is executed
         * asynchronously from the call, therefore it returns immediately. However, the
         * method accepts a callback parameter which will be executed when the refresh is
         * complete.
         *
         * @param callback   function    a callback function called when the refresh is complete
         */
        refresh: function(callback) {
            this._resize();  // just make sure we display the widget right without delay
            AsyncFunction(function() {
                this.optionCache.cleanup();

                var opt, options = this.element[0].childNodes;

                for (var i=0, l1=options.length; i<l1; i++) {
                    opt = options[i];
                    if (opt.nodeType === 1) {
                        if (opt.tagName.toUpperCase() === 'OPTGROUP') {
                            var optGroup = $(opt).data('option-group') || (PRE_OPTGROUP + (this.optionGroupIndex++));
                            var grpOptions = opt.childNodes;

                            this.optionCache.prepareGroup($(opt), optGroup);

                            for (var j=0, l2=grpOptions.length; j<l2; j++) {
                                opt = grpOptions[j];
                                if (opt.nodeType === 1) {
                                    this.optionCache.prepareOption($(opt), optGroup);
                                }
                            }
                        } else {
                            this.optionCache.prepareOption($(opt));  // add to default group
                        }
                    }
                }

                this.optionCache.reIndex();

                if (this._searchField && this._searchField.is(':visible')) {
                    this._search(null, true);
                }

                if (callback) callback();
            }, 10, this);

        },

        /**
         * Search the list of available items and filter them. If the parameter 'text' is
         * undefined, the actual value from the search field is used. If 'text' is specified,
         * the search field is updated.
         *
         * @param options string|object    (optional) the search options
         */
        search: function(options) {
            if (typeof options != 'object') {
                options = {showInput: true, text: options};
            }

            if ((options.toggleInput != false) && !this._searchField.is(':visible')) {
                this._buttons.search.trigger('click');
            }

            this._search(options.text, !!options.silent);
        },

        /**
         * Dynamically change the locale for the widget. If the specified locale is not
         * found, the default locale will be used. If locale is undefined, the current locale
         * will be returned
         */
        locale: function(locale) {

            if (locale === undefined) {
                return this.options.locale;
            } else {
                this._setLocale(locale);

                this._updateControls();
                this._updateHeaders();
            }
        },

        _destroy: function() {
            this.optionCache.reset(true);
            this._lists['selected'].empty().remove();
            this._lists['available'].empty().remove();
            this._elementWrapper.empty().remove();

            delete this.optionCache;
            delete this._searchDelayed;
            delete this._lists;
            delete this._elementWrapper;

            this.element.removeClass('uix-multiselect-original');
        },

        /**
         * ***************************************
         *   PRIVATE
         * ***************************************
         */

        _initSearchable: function() {
            var isToggle = ('toggle' === this.options.searchField);
            var searchHeader = this.options.searchHeader;

            if (isToggle) {
                var that = this;
                this._buttons['search'] = $('<button></button', { type:"button" }).addClass('uix-control-right')
                    .attr('data-localekey', 'search')
                    .attr('title', this._t('search'))
                    .button({icons:{primary:'ui-icon-search'}, text:false})
                    .click(function(e) {
                        e.preventDefault(); e.stopPropagation();
                        if (that._searchField.is(':visible')) {
                            var b = $(this);
                            that._headers[searchHeader].css('visibility', 'visible').fadeTo('fast', 1.0);
                            that._searchField.hide('slide', {direction: 'right'}, 200, function() { b.removeClass('ui-corner-right ui-state-active').addClass('ui-corner-all'); });
                            that._searchDelayed.cancelLastRequest();
                            that.optionCache.filter('');
                        } else {
                            that._headers[searchHeader].fadeTo('fast', 0.1, function() { $(this).css('visibility', 'hidden'); });
                            $(this).removeClass('ui-corner-all').addClass('ui-corner-right ui-state-active');
                            that._searchField.show('slide', {direction: 'right'}, 200, function() { $(this).focus(); });
                            that._search();
                        }
                        return false;
                    })
                    .insertBefore( this._headers[searchHeader] );
            }
            if (this.options.searchField) {
                if (!isToggle) {
                    this._headers[searchHeader].hide();
                }
                this._searchField = $('<input type="text" />').addClass('uix-search ui-widget-content ui-corner-' + (isToggle ? 'left' : 'all'))[isToggle ? 'hide' : 'show']()
                    .insertBefore( this._headers[searchHeader] )
                    .focus(function() { $(this).select(); })
                    .on("keydown keypress", function(e) { if (e.keyCode == 13) { e.preventDefault(); e.stopPropagation(); return false; } })
                    .keyup($.proxy(this._searchDelayed.request, this._searchDelayed));
            }
        },

        _applyListDroppable: function() {
            if (this.options.selectionMode.indexOf('d&d') == -1) return;

            var _optionCache = this.optionCache;
            var currentScope = this.scope;

            var getElementData = function(d) {
                return _optionCache._elements[d.data('element-index')];
            };

            var initDroppable = function(e, s) {
                e.droppable({
                    accept: function(draggable) {
                        var eData = getElementData(draggable);
                        return eData && (eData.selected != s);  // from different seleciton only
                    },
                    activeClass: 'ui-state-highlight',
                    scope: currentScope,
                    drop: function(evt, ui) {
                        ui.draggable.removeClass('ui-state-disabled');
                        ui.helper.remove();
                        _optionCache.setSelected(getElementData(ui.draggable), s);
                    }
                });
            }

            initDroppable(this._lists['selected'], true);
            initDroppable(this._lists['available'], false);

            if (this.options.sortable) {
                var that = this;
                this._lists['selected'].sortable({
                     appendTo: 'parent',
                     axis: "y",
                     containment: $('.multiselect-selected-list', this._elementWrapper), //"parent",
                     items: '.multiselect-element-wrapper',
                     handle: '.group-element',
                     revert: true,
                     stop: $.proxy(function(evt, ui) {
                         var prevGroup;
                         $('.multiselect-element-wrapper', that._lists['selected']).each(function() {
                             var currGroup = that.optionCache._groups.get($(this).data('option-group'));
                             if (!prevGroup) {
                                 that.element.append(currGroup.groupElement);
                             } else {
                                 currGroup.groupElement.insertAfter(prevGroup.groupElement);
                             }
                             prevGroup = currGroup;
                         });
                     }, this)
                 });
            }
        },

        _search: function(term, silent) {
            if (this._searchField.is(':visible')) {
                if (typeof term === "string") {   // issue #36
                    this._searchField.val(term);
                } else {
                    term = this._searchField.val();
                }
            }

            this.optionCache.filter(term, silent);
        },

        _setLocale: function(locale) {
            if (locale == 'auto') {
                locale = navigator.userLanguage ||
                         navigator.language ||
                         navigator.browserLanguage ||
                         navigator.systemLanguage ||
                         '';
            }
            if (!$.uix.multiselect.i18n[locale]) {
                locale = '';   // revert to default is not supported auto locale
            }
            this.options.locale = locale;
        },

        _t: function(key, plural, data) {
            return _({locale:this.options.locale, key:key, plural:plural, data:data});
        },

        _updateControls: function() {
            var that = this;
            $('.uix-control-left,.uix-control-right', this._elementWrapper).each(function() {
                $(this).attr('title', that._t( $(this).attr('data-localekey') ));
            });
        },

        _updateHeaders: function() {
            var t, info = this.optionCache.getSelectionInfo();

            this._headers['selected']
                .text( t = this._t('itemsSelected', info.selected.total, {count:info.selected.total}) )
                .parent().attr('title',
                    this.options.filterSelected
                    ? this._t('itemsSelected', info.selected.count, {count:info.selected.count}) + ", " +
                      this._t('itemsFiltered', info.selected.filtered, {count:info.selected.filtered})
                    : t
                );
            this._headers['available']
                .text( this._t('itemsAvailable', info.available.total, {count:info.available.total}) )
                .parent().attr('title',
                    this._t('itemsAvailable', info.available.count, {count:info.available.count}) + ", " +
                    this._t('itemsFiltered', info.available.filtered, {count:info.available.filtered}) );
        },

        // call this method whenever the widget resizes
        // NOTE : the widget MUST be visible and have a width and height when calling this
        _resize: function() {
            var pos = this.options.availableListPosition.toLowerCase();         // shortcut
            var sSize = ('left,right'.indexOf(pos) >= 0) ? 'Width' : 'Height';  // split size fn
            var tSize = ('left,right'.indexOf(pos) >= 0) ? 'Height' : 'Width';  // total size fn
            var cSl = this.element['outer'+sSize]() * this.options.splitRatio;  // list container size selected
            var cAv = this.element['outer'+sSize]() - cSl;                      // ... available
            var hSl = (tSize === 'Width') ? cSl : this.element.outerHeight();   // scrollable area size selected
            var hAv = (tSize === 'Width') ? cAv : this.element.outerHeight();   // ... available
            var styleRule = ('left,right'.indexOf(pos) >= 0) ? 'left' : 'top';  // CSS rule for offsetting
            var swap = ('left,top'.indexOf(pos) >= 0);                          // true if we swap left-right or top-bottom
            var isToggle = ('toggle' === this.options.searchField);             // true if search field is toggle-able
            var headerBordersBoth = 'ui-corner-tl ui-corner-tr ui-corner-bl ui-corner-br ui-corner-top';
            var hSlCls = (tSize === 'Width') ? (swap ? '' : 'ui-corner-top') : (swap ? 'ui-corner-tr' : 'ui-corner-tl');
            var hAvCls = (tSize === 'Width') ? (swap ? 'ui-corner-top' : '') : (swap ? 'ui-corner-tl' : 'ui-corner-tr');

            // calculate outer lists dimensions
            this._elementWrapper.find('.multiselect-available-list')
                [sSize.toLowerCase()](cAv).css(styleRule, swap ? 0 : cSl)
                [tSize.toLowerCase()](this.element['outer'+tSize]() + 1);  // account for borders
            this._elementWrapper.find('.multiselect-selected-list')
                [sSize.toLowerCase()](cSl).css(styleRule, swap ? cAv : 0)
                [tSize.toLowerCase()](this.element['outer'+tSize]() + 1); // account for borders

            // selection all button
            this._buttons['selectAll'].button('option', 'icons', {primary: transferIcon(pos, 'ui-icon-arrowthickstop-1-', false) });
            this._buttons['deselectAll'].button('option', 'icons', {primary: transferIcon(pos, 'ui-icon-arrowthickstop-1-', true) });

            // header borders
            this._headers['available'].parent().removeClass(headerBordersBoth).addClass(hAvCls);
            this._headers['selected'].parent().removeClass(headerBordersBoth).addClass(hSlCls);

            // make both headers equal!
            if (!isToggle) {
                var h = Math.max(this._headers['selected'].parent().height(), this._headers['available'].parent().height());
                this._headers['available'].parent().height(h);
                this._headers['selected'].parent().height(h);
            }
            // adjust search field width
            if (this._searchField) {
                this._searchField.width( (sSize === 'Width' ? cAv : this.element.width()) - (isToggle ? 52 : 26) );  // issue #50
            }

            // calculate inner lists height
            this._lists['available'].height(hAv - this._headers['available'].parent().outerHeight() - 2);  // account for borders
            this._lists['selected'].height(hSl - this._headers['selected'].parent().outerHeight() - 2);    // account for borders
        },

        /**
         * return false if the event was prevented by an handler, true otherwise
         */
        _triggerUIEvent: function(event, ui) {
            var eventType;

            if (typeof event === 'string') {
                eventType = event;
                event = $.Event(event);
            } else {
                eventType = event.type;
            }

            //console.log($.inArray(event.type, NATIVE_EVENTS));

            //if ($.inArray(event.type, NATIVE_EVENTS) > -1) {
                this.element.trigger(event, ui);
            //} else {
            //    this._trigger(eventType, event, ui);
            //}

            return !event.isDefaultPrevented();
        },

        _setOption: function(key, value) {
            // Use the _setOption method to respond to changes to options
            switch(key) {
                // TODO
            }
            if (typeof(this._superApply) == 'function'){
            	this._superApply(arguments);
            }else{
            	$.Widget.prototype._setOption.apply(this, arguments);
            }
        }
    });



    /**
     * Comparator registry.
     *
     * function(a, b, g)   where a is compared to b and g is true if they are groups
     */
    var ItemComparators = {
        /**
         * Naive general implementation
         */
        standard: function(a, b) {
            if (a > b) return 1;
            if (a < b) return -1;
            return 0;
        },
        /*
         * Natural Sort algorithm for Javascript - Version 0.7 - Released under MIT license
         * Author: Jim Palmer (based on chunking idea from Dave Koelle)
         */
        natural: function naturalSort(a, b) {
            var re = /(^-?[0-9]+(\.?[0-9]*)[df]?e?[0-9]?$|^0x[0-9a-f]+$|[0-9]+)/gi,
                sre = /(^[ ]*|[ ]*$)/g,
                dre = /(^([\w ]+,?[\w ]+)?[\w ]+,?[\w ]+\d+:\d+(:\d+)?[\w ]?|^\d{1,4}[\/\-]\d{1,4}[\/\-]\d{1,4}|^\w+, \w+ \d+, \d{4})/,
                hre = /^0x[0-9a-f]+$/i,
                ore = /^0/,
                i = function(s) { return naturalSort.insensitive && (''+s).toLowerCase() || ''+s },
                // convert all to strings strip whitespace
                x = i(a).replace(sre, '') || '',
                y = i(b).replace(sre, '') || '',
                // chunk/tokenize
                xN = x.replace(re, '\0$1\0').replace(/\0$/,'').replace(/^\0/,'').split('\0'),
                yN = y.replace(re, '\0$1\0').replace(/\0$/,'').replace(/^\0/,'').split('\0'),
                // numeric, hex or date detection
                xD = parseInt(x.match(hre)) || (xN.length != 1 && x.match(dre) && Date.parse(x)),
                yD = parseInt(y.match(hre)) || xD && y.match(dre) && Date.parse(y) || null,
                oFxNcL, oFyNcL;
            // first try and sort Hex codes or Dates
            if (yD)
                if ( xD < yD ) return -1;
                else if ( xD > yD ) return 1;
            // natural sorting through split numeric strings and default strings
            for(var cLoc=0, numS=Math.max(xN.length, yN.length); cLoc < numS; cLoc++) {
                // find floats not starting with '0', string or 0 if not defined (Clint Priest)
                oFxNcL = !(xN[cLoc] || '').match(ore) && parseFloat(xN[cLoc]) || xN[cLoc] || 0;
                oFyNcL = !(yN[cLoc] || '').match(ore) && parseFloat(yN[cLoc]) || yN[cLoc] || 0;
                // handle numeric vs string comparison - number < string - (Kyle Adams)
                if (isNaN(oFxNcL) !== isNaN(oFyNcL)) { return (isNaN(oFxNcL)) ? 1 : -1; }
                // rely on string comparison if different types - i.e. '02' < 2 != '02' < '2'
                else if (typeof oFxNcL !== typeof oFyNcL) {
                    oFxNcL += '';
                    oFyNcL += '';
                }
                if (oFxNcL < oFyNcL) return -1;
                if (oFxNcL > oFyNcL) return 1;
            }
            return 0;
        }
    };


    var transferDir = ['n','e','s','w'];                          // button icon direction
    var transferOrientation = ['bottom','left','top','right'];    // list of matching directions with icons
    var transferIcon = function(pos, prefix, selected) {
        return prefix + transferDir[($.inArray(pos.toLowerCase(), transferOrientation) + (selected ? 2 : 0)) % 4];
    };

    /**
     * setTimeout on steroids!
     */
    var AsyncFunction = function(callback, timeout, self) {
        var args = Array.prototype.slice.call(arguments, 3);
        return setTimeout(function() {
            callback.apply(self || window, args);
        }, timeout);
    };


    var SearchDelayed = function(widget, options) {
        this._widget = widget;
        this._options = options;
        this._lastSearchValue = null;
    };

    SearchDelayed.prototype = {
        request: function() {
            if (this._widget._searchField.val() == this._lastSearchValue) return;  // prevent searching twice same term

            this.cancelLastRequest();

            this._timeout = AsyncFunction(function() {
                this._timeout = null;
                this._lastSearchValue = this._widget._searchField.val();

                this._widget._search();
            }, this._options.delay, this);
        },
        cancelLastRequest: function() {
            if (this._timeout) {
                clearTimeout(this._timeout);
            }
        }
    };

    /**
     * Map of all option groups
     */
    var GroupCache = function(comp) {
        // private members

        var keys = [];
        var items = {};
        var comparator = comp;

        // public methods

        this.setComparator = function(comp) {
            comparator = comp;
            return this;
        };

        this.clear = function() {
            keys = [];
            items = {};
            return this;
        };

        this.containsKey = function(key) {
            return !!items[key];
        };

        this.get = function(key) {
            return items[key];
        };

        this.put = function(key, val) {
            if (!items[key]) {
                if (comparator) {
                    keys.splice((function() {
                        var low = 0, high = keys.length;
                        var mid = -1, c = 0;
                        while (low < high) {
                            mid = parseInt((low + high)/2);
                            var a = items[keys[mid]].groupElement;
                            var b = val.groupElement;
                            c = comparator(a ? a.attr('label') : DEF_OPTGROUP, b ? b.attr('label') : DEF_OPTGROUP);
                            if (c < 0)   {
                                low = mid + 1;
                            } else if (c > 0) {
                                high = mid;
                            } else {
                                return mid;
                            }
                        }
                        return low;
                    })(), 0, key);
                } else {
                    keys.push(key);
                }
            }

            items[key] = val;
            return this;
        };

        this.remove = function(key) {
            delete items[key];
            return keys.splice(keys.indexOf(key), 1);
        };

        this.each = function(callback) {
            var args = Array.prototype.slice.call(arguments, 1);
            args.splice(0, 0, null, null);
            for (var i=0, len=keys.length; i<len; i++) {
                args[0] = keys[i];
                args[1] = items[keys[i]];
                callback.apply(args[1], args);
            }
            return this;
        };

    };

    var OptionCache = function(widget) {
        this._widget = widget;
        this._listContainers = {
            'selected': $('<div></div>').appendTo(this._widget._lists['selected']),
            'available': $('<div></div>').appendTo(this._widget._lists['available'])
        };

        this._elements = [];
        this._groups = new GroupCache();

        this._moveEffect = {
            fn: widget.options.moveEffect,
            options: widget.options.moveEffectOptions,
            speed: widget.options.moveEffectSpeed
        };

        this._selectionMode = this._widget.options.selectionMode.indexOf('dblclick') > -1 ? 'dblclick'
                            : this._widget.options.selectionMode.indexOf('click') > -1 ? 'click' : false;

        this.reset();
    };

    OptionCache.Options = {
        batchCount: 200,
        batchDelay: 50
    };

    OptionCache.prototype = {
        _createGroupElement: function(grpElement, optGroup, selected) {
            var that = this;
            var gData;

            var getLocalData = function() {
                if (!gData) gData = that._groups.get(optGroup);
                return gData;
            };

            var getGroupName = function() {
                return grpElement ? grpElement.attr('label') : that._widget.options.defaultGroupName;
            };

            var labelCount = $('<span></span>').addClass('label')
                .text(getGroupName() + ' (0)')
                .attr('title', getGroupName() + ' (0)');

            var fnUpdateCount = function() {
                var gDataDst = getLocalData()[selected?'selected':'available'];

                gDataDst.listElement[(!selected && (gDataDst.count || that._widget.options.showEmptyGroups)) || (gDataDst.count && ((gData.optionGroup != DEF_OPTGROUP) || that._widget.options.showDefaultGroupHeader)) ? 'show' : 'hide']();

                var t = getGroupName() + ' (' + gDataDst.count + ')';
                labelCount.text(t).attr('title', t);
            };

            var e = $('<div></div>')
                .addClass('ui-widget-header ui-priority-secondary group-element')
                .append( $('<button></button>', { type:"button" }).addClass('uix-control-right')
                    .attr('data-localekey', (selected?'de':'')+'selectAllGroup')
                    .attr('title', this._widget._t((selected?'de':'')+'selectAllGroup'))
                    .button({icons:{primary:transferIcon(this._widget.options.availableListPosition, 'ui-icon-arrowstop-1-', selected)}, text:false})
                    .click(function(e) {
                        e.preventDefault(); e.stopPropagation();

                        var gDataDst = getLocalData()[selected?'selected':'available'];

                        if (gData.count > 0) {
                            var _transferedOptions = [];

                            that._bufferedMode(true);
                            for (var i=gData.startIndex, len=gData.startIndex+gData.count, eData; i<len; i++) {
                                eData = that._elements[i];
                                if (!eData.filtered && !eData.selected != selected) {
                                    that.setSelected(eData, !selected, true);
                                    _transferedOptions.push(eData.optionElement[0]);
                                }
                            }

                            that._updateGroupElements(gData);
                            that._widget._updateHeaders();

                            that._bufferedMode(false);

                            that._widget._triggerUIEvent(EVENT_CHANGE, { optionElements:_transferedOptions, selected:!selected} );
                        }

                        return false;
                    })
                )
                .append(labelCount)
            ;

            var fnToggle,
                groupIcon = (grpElement) ? grpElement.attr('data-group-icon') : null;
            if (this._widget.options.collapsableGroups) {
                var collapseIconAttr = (grpElement) ? grpElement.attr('data-collapse-icon') : null,
                    grpCollapseIcon = (collapseIconAttr) ? 'ui-icon ' + collapseIconAttr : 'ui-icon ui-icon-triangle-1-s';
                var h = $('<span></span>').addClass('ui-icon collapse-handle')
                    .attr('data-localekey', 'collapseGroup')
                    .attr('title', this._widget._t('collapseGroup'))
                    .addClass(grpCollapseIcon)
                    .mousedown(function(e) { e.stopPropagation(); })
                    .click(function(e) { e.preventDefault(); e.stopPropagation(); fnToggle(grpElement); return false; })
                    .prependTo(e.addClass('group-element-collapsable'))
                ;

                fnToggle = function(grpElement) {
                    var gDataDst = getLocalData()[selected?'selected':'available'],
                        collapseIconAttr = (grpElement) ? grpElement.attr('data-collapse-icon') : null,
                        expandIconAttr = (grpElement) ? grpElement.attr('data-expand-icon') : null,
                        collapseIcon = (collapseIconAttr) ? 'ui-icon ' + collapseIconAttr : 'ui-icon ui-icon-triangle-1-s',
                        expandIcon = (expandIconAttr) ? 'ui-icon ' + expandIconAttr : 'ui-icon ui-icon-triangle-1-e';
                    gDataDst.collapsed = !gDataDst.collapsed;
                    gDataDst.listContainer.slideToggle();  // animate options?
                    h.removeClass(gDataDst.collapsed ? collapseIcon : expandIcon)
                     .addClass(gDataDst.collapsed ? expandIcon : collapseIcon);
                };
            }else{
                if (groupIcon) {
                    $('<span></span>').addClass('collapse-handle '+groupIcon)
                        .css('cursor','default')
                        .prependTo(e.addClass('group-element-collapsable'));
                }
            }
            return $('<div></div>')
                // create an utility function to update group element count
                .data('fnUpdateCount', fnUpdateCount)
                .data('fnToggle', fnToggle || $.noop)
                .append(e)
            ;
        },

        _createGroupContainerElement: function(grpElement, optGroup, selected) {
            var that = this;
            var e = $('<div></div>');
            var _received_index;

            if (this._widget.options.sortable && selected) {
                e.sortable({
                    tolerance: "pointer",
                    appendTo: this._widget._elementWrapper,
                    connectWith: this._widget._lists['available'].attr('id'),
                    scope: this._widget.scope,
                    helper: 'clone',
                    receive: function(evt, ui) {
                        var e = that._elements[_received_index = ui.item.data('element-index')];

                        e.selected = true;
                        e.optionElement.prop('selected', true);
                        e.listElement.removeClass('ui-state-active');
                    },
                    stop: function(evt, ui) {
                        var e;
                        if (_received_index) {
                            e = that._elements[_received_index];
                            _received_index = undefined;
                            ui.item.replaceWith(e.listElement.addClass('ui-state-highlight option-selected'));
                            that._widget._updateHeaders();
                            that._widget._triggerUIEvent(EVENT_CHANGE, { optionElements:[e.optionElement[0]], selected:true } );
                        } else {
                            e = that._elements[ui.item.data('element-index')];
                            if (e && !e.selected) {
                                that._bufferedMode(true);
                                that._appendToList(e);
                                that._bufferedMode(false);
                            }
                        }
                        if (e) that._reorderSelected(e.optionGroup);
                    },
                    revert: true
                });
            }

            if (this._selectionMode) {
                $(e).on(this._selectionMode, 'div.option-element', function() {
                    var eData = that._elements[$(this).data('element-index')];
                    eData.listElement.removeClass('ui-state-hover');
                    that.setSelected(eData, !selected);
                });
            }

            return e;
        },

        _createElement: function(optElement, optGroup) {
            var o = this._widget.options.optionRenderer
                  ? this._widget.options.optionRenderer(optElement, optGroup)
                  : $('<div></div>').text(optElement.text());
            var optIcon = optElement.attr("data-option-icon");
            var e = $('<div></div>').append(o).addClass('ui-state-default option-element')
                .attr("unselectable", "on")  // disable text selection on this element (IE, Opera)
                .data('element-index', -1)
                .hover(
                    function() {
                        if (optElement.prop('selected')) $(this).removeClass('ui-state-highlight');
                        $(this).addClass('ui-state-hover');
                    },
                    function() {
                        $(this).removeClass('ui-state-hover');
                        if (optElement.prop('selected')) $(this).addClass('ui-state-highlight');
                    }
                );
            if (this._widget.options.selectionMode.indexOf('d&d') > -1) {
                var that = this;
                e.draggable({
                    addClasses: false,
                    cancel: (this._widget.options.sortable ? '.option-selected, ' : '') + '.ui-state-disabled',
                    appendTo: this._widget._elementWrapper,
                    scope: this._widget.scope,
                    start: function(evt, ui) {
                        $(this).addClass('ui-state-disabled ui-state-active');
                        ui.helper.width($(this).width()).height($(this).height());
                    },
                    stop: function(evt, ui) {
                        $(this).removeClass('ui-state-disabled ui-state-active');
                    },
                    helper: 'clone',
                    revert: 'invalid',
                    zIndex: 99999,
                    disabled: optElement.prop('disabled')
                });
                if (optElement.prop('disabled')) {
                    e.addClass('ui-state-disabled');
                }
                if (this._widget.options.sortable) {
                    e.draggable('option', 'connectToSortable', this._groups.get(optGroup)['selected'].listContainer);
                }
            } else if (optElement.prop('disabled')) {
                e[(optElement.prop('disabled') ? "add" : "remove") + "Class"]('ui-state-disabled');
            }
            if (optIcon) {
                e.addClass('grouped-option').prepend($('<span></span>').addClass('ui-icon ' + optIcon));
            }
            return e;
        },

        _isOptionCollapsed: function(eData) {
            return this._groups.get(eData.optionGroup)[eData.selected?'selected':'available'].collapsed;
        },

        _updateGroupElements: function(gData) {
            if (gData) {
                gData['selected'].count = 0;
                gData['available'].count = 0;
                for (var i=gData.startIndex, len=gData.startIndex+gData.count; i<len; i++) {
                    gData[this._elements[i].selected?'selected':'available'].count++;
                }
                gData['selected'].listElement.data('fnUpdateCount')();
                gData['available'].listElement.data('fnUpdateCount')();
            } else {
                this._groups.each(function(k,gData,that) {
                    that._updateGroupElements(gData);
                }, this);
            }
        },

        _appendToList: function(eData) {
            var that = this;
            var gData = this._groups.get(eData.optionGroup);

            var gDataDst = gData[eData.selected?'selected':'available'];

            if ((eData.optionGroup != this._widget.options.defaultGroupName) || this._widget.options.showDefaultGroupHeader) {
                gDataDst.listElement.show();
            }
            if (gDataDst.collapsed) {
                gDataDst.listElement.data('fnToggle')(); // animate show?
            } else {
                gDataDst.listContainer.show();
            }

            var insertIndex = eData.index - 1;
            while ((insertIndex >= gData.startIndex) &&
                   (this._elements[insertIndex].selected != eData.selected)) {
                insertIndex--;
            }

            if (insertIndex < gData.startIndex) {
                gDataDst.listContainer.prepend(eData.listElement);
            } else {
                var prev = this._elements[insertIndex].listElement;
                // FIX : if previous element is animated, get it's animated parent as reference
                if (prev.parent().hasClass('ui-effects-wrapper')) {
                    prev = prev.parent();
                }
                eData.listElement.insertAfter(prev);
            }
            eData.listElement[(eData.selected?'add':'remove')+'Class']('ui-state-highlight option-selected');

            if ((eData.selected || !eData.filtered) && !this._isOptionCollapsed(eData) && this._moveEffect && this._moveEffect.fn) {
                eData.listElement.hide().show(this._moveEffect.fn, this._moveEffect.options, this._moveEffect.speed);
            } else if (eData.filtered) {
                eData.listElement.hide();
            }
        },

        _reorderSelected: function(optGroup) {
            var e = this._elements;
            var g = this._groups.get(optGroup);
            var container = g.groupElement ? g.groupElement : this._widget.element;
            var prevElement;
            $('.option-element', g['selected'].listContainer).each(function() {
                var currElement = e[$(this).data('element-index')].optionElement;
                if (!prevElement) {
                    container.prepend(currElement);
                } else {
                    currElement.insertAfter(prevElement);
                }
                prevElement = currElement;
            });
        },

        _bufferedMode: function(enabled) {
            if (enabled) {
                this._oldMoveEffect = this._moveEffect; this._moveEffect = null;

                // backup lists' scroll position before going into buffered mode
                this._widget._lists['selected'].data('scrollTop', this._widget._lists['selected'].scrollTop());
                this._widget._lists['available'].data('scrollTop', this._widget._lists['available'].scrollTop());

                this._listContainers['selected'].detach();
                this._listContainers['available'].detach();
            } else {
                // restore scroll position (if available)
                this._widget._lists['selected'].append(this._listContainers['selected'])
                        .scrollTop( this._widget._lists['selected'].data('scrollTop') || 0 );
                this._widget._lists['available'].append(this._listContainers['available'])
                        .scrollTop( this._widget._lists['available'].data('scrollTop') || 0 );

                this._moveEffect = this._oldMoveEffect;

                delete this._oldMoveEffect;
            }

        },

        reset: function(destroy) {
            this._groups.clear();
            this._listContainers['selected'].empty();
            this._listContainers['available'].empty();

            if (destroy) {
                for (var i=0, e=this._elements, len=e.length; i<len; i++) {
                    e[i].optionElement.removeData('element-index');
                }
                delete this._elements;
                delete this._groups;
                delete this._listContainers;
            } else {
                this._elements = [];
                this.prepareGroup();  // reset default group
                this._groups.setComparator(this.getComparator());
            }
        },

        // should call _reIndex after this
        cleanup: function() {
            var p = this._widget.element[0];
            var _groupsRemoved = [];
            this._groups.each(function(g,v) {
                if (v.groupElement && !$.contains(p, v.groupElement[0])) {
                    _groupsRemoved.push(g);
                }
            });
            for (var i=0, eData; i<this._elements.length; i++) {
                eData = this._elements[i];
                if (!$.contains(p, eData.optionElement[0]) || ($.inArray(eData.optionGroup, _groupsRemoved) > -1)) {
                    this._elements.splice(i--, 1)[0].listElement.remove();
                }
            }
            for (var i=0, len=_groupsRemoved.length; i<len; i++) {
                this._groups.remove(_groupsRemoved[i]);
            }

            this.prepareGroup();  // make sure we have the default group still!
        },

        getComparator: function() {
            return this._widget.options.sortMethod
                 ? typeof this._widget.options.sortMethod == 'function'
                   ? this._widget.options.sortMethod
                   : ItemComparators[this._widget.options.sortMethod]
                 : null;
        },

        // prepare option group to be rendered (should call reIndex after this!)
        prepareGroup: function(grpElement, optGroup) {
            optGroup = optGroup || DEF_OPTGROUP;
            if (!this._groups.containsKey(optGroup)) {
                this._groups.put(optGroup, {
                    startIndex: -1,
                    count: 0,
                    'selected': {
                        collapsed: false,
                        count: 0,
                        listElement: this._createGroupElement(grpElement, optGroup, true),
                        listContainer: this._createGroupContainerElement(grpElement, optGroup, true)
                    },
                    'available': {
                        collapsed: false,
                        count: 0,
                        listElement: this._createGroupElement(grpElement, optGroup, false),
                        listContainer: this._createGroupContainerElement(grpElement, optGroup, false)
                    },
                    groupElement: grpElement,
                    optionGroup: optGroup     // for back ref
                });
            }
        },

        // prepare option element to be rendered (must call reIndex after this!)
        // If optGroup is defined, prepareGroup(optGroup) should have been called already
        prepareOption: function(optElement, optGroup) {
            var e;
            if (optElement.data('element-index') === undefined) {
                optGroup = optGroup || DEF_OPTGROUP;
                this._elements.push(e = {
                    index: -1,
                    selected: false,
                    filtered: false,
                    listElement: this._createElement(optElement, optGroup),
                    optionElement: optElement,
                    optionGroup: optGroup
                });
            } else {
                this._elements[optElement.data('element-index')]
                    .listElement[(optElement.prop('disabled') ? "add" : "remove") + "Class"]('ui-state-disabled')
                ;
            }

        },

        reIndex: function() {
            // note : even if not sorted, options are added as they appear,
            //        so they should be grouped just fine anyway!
            var comparator = this.getComparator();
            if (comparator) {
                var _groups = this._groups;
                this._elements.sort(function(a, b) {
                    // sort groups
                    var ga = _groups.get(a.optionGroup).groupElement;
                    var gb = _groups.get(b.optionGroup).groupElement;
                    var g = comparator(ga ? ga.attr('label') : DEF_OPTGROUP, gb ? gb.attr('label') : DEF_OPTGROUP);
                    if (g != 0) return g;
                    else        return comparator(a.optionElement.text(), b.optionElement.text());
                });
            }

            this._bufferedMode(true);

            this._groups.each(function(g, v, l, showDefGroupName) {
                if (!v['available'].listContainer.parents('.multiselect-element-wrapper').length) {  // if no parent, then it was never attached yet.
                    if (v.groupElement) {
                        v.groupElement.data('option-group', g);  // for back ref
                    }

                    var wrapper_selected = $('<div></div>').addClass('multiselect-element-wrapper').data('option-group', g);
                    var wrapper_available = $('<div></div>').addClass('multiselect-element-wrapper').data('option-group', g);
                    wrapper_selected.append(v.selected.listElement.hide());
                    if (g != DEF_OPTGROUP || (g == DEF_OPTGROUP && showDefGroupName)) {
                        wrapper_available.append(v['available'].listElement.show());
                    }
                    wrapper_selected.append(v['selected'].listContainer);
                    wrapper_available.append(v['available'].listContainer);

                    l['selected'].append(wrapper_selected);
                    l['available'].append(wrapper_available);
                }
                v.count = 0;
            }, this._listContainers, this._widget.options.showDefaultGroupHeader);

            for (var i=0, eData, gData, len=this._elements.length; i<len; i++) {
                eData = this._elements[i];
                gData = this._groups.get(eData.optionGroup);

                // update group index and count info
                if (gData.startIndex == -1 || gData.startIndex >= i) {
                    gData.startIndex = i;
                    gData.count = 1;
                } else {
                    gData.count++;
                }

                // save element index for back ref
                eData.listElement.data('element-index', eData.index = i);

                if (eData.optionElement.data('element-index') == undefined || eData.selected != eData.optionElement.prop('selected')) {
                    eData.selected = eData.optionElement.prop('selected');
                    eData.optionElement.data('element-index', i);  // also save for back ref here

                    this._appendToList(eData);
                }
            }

            this._updateGroupElements();
            this._widget._updateHeaders();
            this._groups.each(function(g,v,t) { t._reorderSelected(g); }, this);

            this._bufferedMode(false);

        },

        filter: function(term, silent) {

            if (term && !silent) {
                var ui = { term:term };
                if (this._widget._triggerUIEvent(EVENT_SEARCH, ui )) {
                    term = ui.term;  // update term
                } else {
                    return;
                }
            }

            this._bufferedMode(true);

            var filterSelected = this._widget.options.filterSelected;
            var filterFn = this._widget.options.searchFilter || function(term, opt) {
                //return !(!text || (eData.optionElement.text().toLowerCase().indexOf(text) > -1));
                return opt.innerHTML.toLowerCase().indexOf(term) > -1;
            };
            term = (this._widget.options.searchPreFilter || function(term) {
                return term ? (term+"").toLowerCase() : false;
            })(term);

            for (var i=0, eData, len=this._elements.length, filtered; i<len; i++) {
                eData = this._elements[i];
                filtered = !(!term || filterFn(term, eData.optionElement[0]));

                if ((!eData.selected || filterSelected) && (eData.filtered != filtered)) {
                    eData.listElement[filtered ? 'hide' : 'show']();
                    eData.filtered = filtered;
                } else if (eData.selected) {
                    eData.filtered = false;
                }
            }

            this._widget._updateHeaders();
            this._bufferedMode(false);

        },

        getSelectionInfo: function() {
            var info = {'selected': {'total': 0, 'count': 0, 'filtered': 0}, 'available': {'total': 0, 'count': 0, 'filtered': 0} };

            for (var i=0, len=this._elements.length; i<len; i++) {
                var eData = this._elements[i];
                info[eData.selected?'selected':'available'][eData.filtered?'filtered':'count']++;
                info[eData.selected?'selected':'available'].total++;
            }

            return info;
        },

        setSelected: function(eData, selected, silent) {
            if (eData.optionElement.attr('disabled') && selected) {
                return;
            }

            eData.optionElement.prop('selected', eData.selected = selected);

            this._appendToList(eData);

            if (!silent) {
                if (this._widget.options.sortable && selected) {
                    this._reorderSelected(eData.optionGroup);
                }
                this._updateGroupElements(this._groups.get(eData.optionGroup));
                this._widget._updateHeaders();
                this._widget._triggerUIEvent(EVENT_CHANGE, { optionElements:[eData.optionElement[0]], selected:selected } );
            }
        },

        // utility function to select all options
        setSelectedAll: function(selected) {
            var _transferedOptions = [];
            var _modifiedGroups = {};

            this._bufferedMode(true);

            for (var i=0, eData, len=this._elements.length; i<len; i++) {
                eData = this._elements[i];
                if (!((eData.selected == selected) || (eData.optionElement.attr('disabled') || (selected && (eData.filtered || eData.selected))))) {
                    this.setSelected(eData, selected, true);
                    _transferedOptions.push(eData.optionElement[0]);
                    _modifiedGroups[eData.optionGroup] = true;
                }
            }

            if (this._widget.options.sortable && selected) {
                var that = this;
                $.each(_modifiedGroups, function(g) {  that._reorderSelected(g); });
            }

            this._updateGroupElements();
            this._widget._updateHeaders();
            this._bufferedMode(false);

            this._widget._triggerUIEvent(EVENT_CHANGE, { optionElements:_transferedOptions, selected:selected } );
        }

    };

    /**
     * Expects paramter p to be
     *
     *   locale        (string) the locale to use (default = '')
     *   key           (string) the locale string key
     *   plural        (int)    the plural value to use
     *   data          (object) the data object to use as variables
     *
     */
    function _(p) {
        var locale = $.uix.multiselect.i18n[p.locale] ? p.locale : '';
        var i18n = $.uix.multiselect.i18n[locale];
        var plural = p.plural || 0;
        var data = p.data || {};
        var t;

        if (plural === 2 && i18n[p.key+'_plural_two']) {
            t = i18n[p.key+'_plural_two'];
        } else if ((plural === 2 || plural === 3) && i18n[p.key+'_plural_few']) {
            t = i18n[p.key+'_plural_few']
        } else if (plural > 1 && i18n[p.key+'_plural']) {
            t = i18n[p.key+'_plural'];
        } else if (plural === 0 && i18n[p.key+'_nil']) {
            t = i18n[p.key+'_nil'];
        } else {
            t = i18n[p.key] || '';
        }

        return t.replace(/\{([^\}]+)\}/g, function(m, n) { return data[n]; });
    };

    /**
     * Default translation
     */
    $.uix.multiselect.i18n = {
        '': {
            itemsSelected_nil: 'no selected option',           // 0
            itemsSelected: '{count} selected option',          // 0, 1
            itemsSelected_plural: '{count} selected options',  // n
            //itemsSelected_plural_two: ...                    // 2
            //itemsSelected_plural_few: ...                    // 3, 4
            itemsAvailable_nil: 'no item available',
            itemsAvailable: '{count} available option',
            itemsAvailable_plural: '{count} available options',
            //itemsAvailable_plural_two: ...
            //itemsAvailable_plural_few: ...
            itemsFiltered_nil: 'no option filtered',
            itemsFiltered: '{count} option filtered',
            itemsFiltered_plural: '{count} options filtered',
            //itemsFiltered_plural_two: ...
            //itemsFiltered_plural_few: ...
            selectAll: 'Select All',
            deselectAll: 'Deselect All',
            search: 'Search Options',
            collapseGroup: 'Collapse Group',
            expandGroup: 'Expand Group',
            selectAllGroup: 'Select All Group',
            deselectAllGroup: 'Deselect All Group'
        }
    };

})(jQuery, window);


var ContextMenu = {

	// private attributes
	_menus : new Array,
	_attachedElement : null,
	_menuElement : null,


	// public method. Sets up whole context menu stuff..
	setup : function (conf) {

		if ( document.all && document.getElementById && !window.opera ) {
			ContextMenu.IE = true;
		}

		if ( !document.all && document.getElementById && !window.opera ) {
			ContextMenu.FF = true;
		}

		if ( document.all && document.getElementById && window.opera ) {
			ContextMenu.OP = true;
		}

		if ( ContextMenu.IE || ContextMenu.FF ) {

			document.oncontextmenu = ContextMenu._show;
			document.onclick = ContextMenu._hide;
		}

	},


	// public method. Attaches context menus to specific class names
	attach : function (classNames, menuId) {

		if (typeof(classNames) == "string") {
			ContextMenu._menus[classNames] = menuId;
		}

		if (typeof(classNames) == "object") {
			for (x = 0; x < classNames.length; x++) {
				ContextMenu._menus[classNames[x]] = menuId;
			}
		}

	},


	// private method. Get which context menu to show
	_getMenuElementId : function (e) {

		if (ContextMenu.IE) {
			ContextMenu._attachedElement = event.srcElement;
		} else {
			ContextMenu._attachedElement = e.target;
		}

		while(ContextMenu._attachedElement != null) {
			var className = ContextMenu._attachedElement.className;

			if (typeof(className) != "undefined") {
				className = className.replace(/^\s+/g, "").replace(/\s+$/g, "")
				var classArray = className.split(/[ ]+/g);

				for (i = 0; i < classArray.length; i++) {
					if (ContextMenu._menus[classArray[i]]) {
						return ContextMenu._menus[classArray[i]];
					}
				}
			}

			if (ContextMenu.IE) {
				ContextMenu._attachedElement = ContextMenu._attachedElement.parentElement;
			} else {
				ContextMenu._attachedElement = ContextMenu._attachedElement.parentNode;
			}
		}

		return null;

	},


	// private method. Shows context menu
	_getReturnValue : function (e) {

		var returnValue = true;
		var evt = ContextMenu.IE ? window.event : e;

		if (evt.button != 1) {
			if (evt.target) {
				var el = evt.target;
			} else if (evt.srcElement) {
				var el = evt.srcElement;
			}

			var tname = el.tagName.toLowerCase();

			if ((tname == "input" || tname == "textarea")) {
				return true;
				}
			} else {
				return  false;
				}

	},


	// private method. Shows context menu
	_show : function (e) {

		ContextMenu._hide();
		var menuElementId = ContextMenu._getMenuElementId(e);

		if (menuElementId) {
			var m = ContextMenu._getMousePosition(e);
			var s = ContextMenu._getScrollPosition(e);

			ContextMenu._menuElement = document.getElementById(menuElementId);

			var item = ContextMenu._attachedElement.innerHTML.replace(/\&nbsp;/g," ");
			var l = ContextMenu._menuElement.getElementsByTagName("a");
			for (x=0; x<l.length; x++) {
			  l[x].href = l[x].id.replace(/%s/,item);
			  }

			ContextMenu._menuElement.style.left = m.x + s.x + 'px';
			ContextMenu._menuElement.style.top = m.y + s.y + 'px';
			ContextMenu._menuElement.style.display = 'block';
			return false;
		}

		return ContextMenu._getReturnValue(e);

	},


	// private method. Hides context menu
	_hide : function () {

		if (ContextMenu._menuElement) {
			ContextMenu._menuElement.style.display = 'none';
		}

	},


	// private method. Returns mouse position
	_getMousePosition : function (e) {

		e = e ? e : window.event;
		var position = {
			'x' : e.clientX,
			'y' : e.clientY
		}

		return position;

	},


	// private method. Get document scroll position
	_getScrollPosition : function () {

		var x = 0;
		var y = 0;

		if( typeof( window.pageYOffset ) == 'number' ) {
			x = window.pageXOffset;
			y = window.pageYOffset;
		} else if( document.documentElement && ( document.documentElement.scrollLeft || document.documentElement.scrollTop ) ) {
			x = document.documentElement.scrollLeft;
			y = document.documentElement.scrollTop;
		} else if( document.body && ( document.body.scrollLeft || document.body.scrollTop ) ) {
			x = document.body.scrollLeft;
			y = document.body.scrollTop;
		}

		var position = {
			'x' : x,
			'y' : y
		}

		return position;

	}

}
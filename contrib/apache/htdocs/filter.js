
var objDoc;

// Defines the maximum number of options we want to show in selection boxes
var MAXLIST = 300;
var items = 0;
var locations = 0;
var buffers = 0;
var itemfilter = "";
var locationfilter = "";
var bufferfilter = "";

function kiwi(ctrl,column)
{
  // Figure out where we are
  supply_row = ctrl.parentElement.parentElement;
  demand_row = supply_row.nextSibling;
  onhand_row = demand_row.nextSibling;
  // Hide a row:
  // demand_row.style.display="none";
  
  // Recompute the ending onhand values
  var ending_onhand = 
    (column==1) ? 0 : parseFloat(onhand_row.cells[column+2].innerHTML);
  for (var i = column+3; i <= 6; ++i) {
    ending_onhand -= parseFloat(demand_row.cells[i].innerHTML);
    ending_onhand += parseFloat(supply_row.cells[i].firstChild.value);
    onhand_row.cells[i].innerHTML = ending_onhand; 
    
    // Display neg numbers in a different style
    onhand_row.cells[i].className = (ending_onhand < 0) ? "problem" : "okay";
  }
}


function display() 
{  
  // Create xml from the selected buffers
  var listBox = document.getElementById("Buffers");
  var output = "<?xml version='1.0' encoding='UTF-8' ?>" +
    "<PLAN xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>\n" +
    "<BUFFERS>\n";
  var noBufferFilter = (document.getElementById("BufferFilter").value == "");
  for (var i = 0; i < listBox.options.length; ++i)
    if (noBufferFilter || listBox.options[i].selected)
      output += '<BUFFER NAME="' + listBox.options[i].text + '"/>\n';
  output += "</BUFFERS></PLAN>\n";
  
  // Create a transport object
  var xmlhttp = createXMLHttpRequest();

  // Send the xml to the server
  xmlhttp.onreadystatechange=function() {
   if (xmlhttp.readyState==4) {
     var xsl = new ActiveXObject("Microsoft.XMLDOM");
     xsl.async = false;
     xsl.load("inventory.xsl");
     top.data.document.open();
     top.data.document.write(xmlhttp.responseXML.transformNode(xsl));
     top.data.document.close();
   }
  }
  xmlhttp.open("GET", "reports/inventorydata.xml",true);
  xmlhttp.send(output);
}


// Create a transport object
function createXMLHttpRequest()
{
  try {
    // For all browsers except for IE v<7
    return new XMLHttpRequest();
  } catch (e1) { try {
    return new ActiveXObject("Msxml2.XMLHTTP.5.0");
  } catch (e2) { try {
    return new ActiveXObject("Msxml2.XMLHTTP.4.0");
  } catch (e3) { try {
    return new ActiveXObject("Msxml2.XMLHTTP.3.0");
  } catch (e4) { try {
    return new ActiveXObject("Msxml2.XMLHTTP.");
  } catch (e5) { try {
    return new ActiveXObject("Microsoft.XMLHTTP");
  } catch (e6) {
    alert("Your browser doesn't support the XMLHttpRequest method");
    return false;
  }}}}}}
}


function GetFilterData() {
  
  // Create a transport object
  var xmlhttp = createXMLHttpRequest();

  // Create the request and wait for the reply
  xmlhttp.onreadystatechange = function() {
   if (xmlhttp.readyState==4) {
     if (xmlhttp.status == 200 || xmlhttp.status == 0) {
       objDoc = xmlhttp.responseXML;
       // xxx todo objDoc.setProperty("SelectionLanguage", "XPath");
       updateLocationList();
       updateItemList();
       updateBufferList();
       updateCookie();
     } else
       alert('There was a problem retrieving the filter data:\n' 
        + xmlhttp.statusText);
    }
  }
  xmlhttp.open("GET", "reports/inventoryfilter.xml",true);
  xmlhttp.send(null)
}

 
function updateCookie()
{
  // @todo not working yet
  var date = new Date() ;
  date.setTime(date.getTime() + 5 * 86400000);
  document.cookie = 
    'expires=' +  date.toGMTString() 
    + '; domain=frepple; path=/; itemfilter=kikiw; locationfilter=kikiw; ';
}


function updateLocationList()
{
  var beginning=new Date();  
  var html = "<select id='Locations' size='6' style='width:100%;' " +
    "multiple onChange='locationUpdate()'>";
  //xxxvar nodes = objDoc.documentElement.selectNodes('LOCATIONS/LOCATION/@NAME');
  var nodes = objDoc.evaluate('PLAN/LOCATIONS/LOCATION/@NAME',
    objDoc, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
  locationfilter = document.getElementById('LocationFilter').value;
  var reg = new RegExp(locationfilter);
  var noFilter = (locationfilter == "");
  var cnt = 0;
  //for (var i = nodes.nextNode(); i != null; i = nodes.iterateNext()); nodes.nextNode()) {
  var i;
  while ((i = nodes.iterateNext())) {
    if (noFilter || reg.test(i.value))
      if (cnt++ < MAXLIST) html += "<option>" + i.value + "</option>";
  }
  if (cnt > MAXLIST) 
    html += "<option>... and " + (cnt-MAXLIST) + " more</option>"; 
  html += "</select>";
  document.getElementById('table').rows[2].cells[0].innerHTML = html;
  document.getElementById('LocCount').innerHTML = cnt;
  loactions = cnt;
}


function updateItemList()
{
  var html = "<select id='Items' size='6' style='width:100%;' " +
    "multiple onChange='itemUpdate()'>";
  //xxx var nodes = objDoc.documentElement.selectNodes('ITEMS/ITEM/@NAME');
  var nodes = objDoc.evaluate('PLAN/ITEMS/ITEM/@NAME',
    objDoc, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
  itemfilter = document.getElementById('ItemFilter').value;
  var reg = new RegExp(itemfilter);
  var noFilter = (itemfilter == "");
  var cnt = 0;
  //xxxfor (var i = nodes.nextNode(); i != null; i = nodes.nextNode()) {
  var i;
  while ((i = nodes.iterateNext())) {
    if (noFilter || reg.test(i.value)) 
      if (cnt++ < MAXLIST) html += "<option>" + i.value + "</option>";
  }
  if (cnt > MAXLIST) 
    html += "<option>... and " + (cnt-MAXLIST) + " more</option>"; 
  html += "</select>";
  document.getElementById('table').rows[2].cells[1].innerHTML = html;
  document.getElementById('ItemCount').innerHTML = cnt;
  items = cnt;
}


function updateBufferList() 
{
  var html = "<select id='Buffers' size='6' style='width:100%;' " + 
   "multiple onChange='bufferUpdate()'>";
  // xxx var nodes = objDoc.documentElement.selectNodes("BUFFERS/BUFFER");
  var nodes = objDoc.evaluate('PLAN/BUFFERS/BUFFER',
    objDoc, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
  bufferfilter = document.getElementById("BufferFilter").value;
  var bufferRegExp = new RegExp(bufferfilter);
  var noBufferFilter = (bufferfilter == "");
  var itemRegExp = new RegExp(document.getElementById("ItemFilter").value);
  var noItemFilter = (document.getElementById("ItemFilter").value == "");
  var locRegExp = new RegExp(document.getElementById("LocationFilter").value);
  var noLocFilter = (document.getElementById("LocationFilter").value == "");
  var cnt = 0;
  var listBox = document.getElementById("Buffers");
  //xxxfor (var i = nodes.nextNode(); i != null; i = nodes.nextNode()) {
  var i;
  while ((i = nodes.iterateNext())) {
    var buf = i.getAttribute("NAME");
    if (noBufferFilter || bufferRegExp.test(buf)) {
      if (noItemFilter || itemRegExp.test(i.getAttribute("ITEM"))) {
        if (noLocFilter || locRegExp.test(i.getAttribute("LOCATION")))
          if (cnt++ < MAXLIST) html += "<option>" + buf + "</option>";
      } 
    } 
  }
  if (cnt > MAXLIST) 
    html += "<option>... and " + (cnt-MAXLIST) + " more</option>"; 
  html += "</select>";
  document.getElementById('table').rows[2].cells[2].innerHTML = html;
  document.getElementById("BufferCount").innerHTML = cnt;
  buffers = cnt;
}


function itemUpdate() 
{
  var cnt = 0;
  var listBox = document.getElementById("Items");
  var fltr = "";
  var max = listBox.options.length;
  if (max > MAXLIST) max = MAXLIST;
  for (var i = 0; i < max; ++i)
    if (listBox.options[i].selected) {
      ++cnt;
      fltr += ((fltr=="") ? "^" : "|^") + listBox.options[i].text + "$";      
    }
  if (listBox.options.length > MAXLIST && listBox.options[MAXLIST].selected) {
    document.getElementById("ItemFilter").value = itemfilter;
    document.getElementById("ItemCount").innerHTML = items;
  }
  else {
    document.getElementById("ItemFilter").value = fltr;
    document.getElementById("ItemCount").innerHTML = cnt;
  }
  updateBufferList();
}


function locationUpdate() 
{
  var cnt = 0;
  var listBox = document.getElementById("Locations");
  var fltr = "";
  var max = listBox.options.length;
  if (max > MAXLIST) max = MAXLIST;
  for (var i = 0; i < max; ++i)
    if (listBox.options[i].selected) {
      ++cnt;
      fltr += ((fltr=="") ? "^" : "|^") + listBox.options[i].text + "$";      
    }
  if (listBox.options.length > MAXLIST && listBox.options[MAXLIST].selected) {
    document.getElementById("LocationFilter").value = locationfilter;
    document.getElementById("LocCount").innerHTML = locations;
  }
  else {
    document.getElementById("LocationFilter").value = fltr;
    document.getElementById("LocCount").innerHTML = cnt;
  }
  updateBufferList();
}


function bufferUpdate() 
{
  var cnt = 0;
  var listBox = document.getElementById("Buffers");
  var fltr = "";
  var max = listBox.options.length;
  if (max > MAXLIST) max = MAXLIST;
  for (var i = 0; i < max; ++i)
    if (listBox.options[i].selected) {
      ++cnt;
      fltr += ((fltr=="") ? "^" : "|^") + listBox.options[i].text + "$";
    }
  if (listBox.options.length > MAXLIST && listBox.options[MAXLIST].selected) {
    document.getElementById("BufferFilter").value = bufferfilter;
    document.getElementById("BufferCount").innerHTML = buffers;
  }
  else {
    document.getElementById("BufferFilter").value = fltr;
    document.getElementById("BufferCount").innerHTML = cnt;
  }
}

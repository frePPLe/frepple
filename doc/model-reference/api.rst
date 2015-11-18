=========================
API: XML, Python and REST
=========================

FrePPLe provides multiple APIs to communicate with the application or the
core planning engine:

* **REST web service**:

  The user interface exposes a rich set of REST web services to created,
  read, update and delete objects from the frePPLe database.

  More detail is available on :doc:`this page </technical-guide/rest-api/index>`.

* **XML**:

  The core planning engine natively reads and writes XML data files. The
  files frepple.xsd and frepple_core.xsd define the XML Schema of the
  data format.

  The XML-data can be placed in any namespace. To support subclassing the
  namespace xsi must be defined as “http\://www.w3.org/2001/XMLSchema-instance”.

  FrePPLe XML files thus typically have the following structure:

  .. code-block:: XML

      <?xml version="1.0" encoding="UTF-8"?>
      <plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      ...
      </plan>

  The following encodings are supported for XML data: ASCII, UTF-8, UTF-16
  (Big/Small Endian), UTF-32(Big/Small Endian), EBCDIC code pages IBM037,
  IBM1047 and IBM1140, ISO-8859-1 (aka Latin1) and Windows-1252. UTF-8 will
  be the best choice in most situations.

* **Python**:

  The frePPLe planning engine embeds an interpreter for the Python language.
  All objects in the planning engine can be read, created, updated and deleted
  from Python code. All functionality of Python and its extension modules is
  accessible from the planning engine.

  It is also possible to access the frePPLe functionality as a Python module.
  A regular "import frepple" statement suffices to load the module.

  Detailed programming and scripting is possible in this way. For complex
  integration tasks and for customization of the algorithms Python is your
  big friend.

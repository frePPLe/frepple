==============================
Translating the user interface
==============================

This section provides step by step instructions on how to translate the user interface to your favourite language.
 
.. Hint::

   We are very keen on receiving translations for additional languages. And it's an easy way for you to contribute
   back to the frePPLe community.

For translators
---------------

**1. Install a translation editor**

  For the translation process you should install an editor for gettext catalogs (.po files).

  Highly recommended is the free `Poedit tool <https://poedit.net/>`_.

**2. Start translating**

  Pick up file the translation file of the language you wish to update from the github
  source code repository. All terms to be translated are collected in this single file. 

   - French: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/fr/fr.po
   - German: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/de/de.po
   - Hebrew: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/he/he.po
   - Italian: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/it/it.po
   - Japanese: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/ja/ja.po
   - Dutch: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/nl/nl.po
   - Portuguese: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/pt/pt.po
   - Brazilian Portuguese: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/pt-br/pt-br.po
   - Russian: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/ru/ru.po
   - Spanish: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/es/es.po
   - Simplified Chinese: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/zh-hans/zh-hans.po
   - Traditional Chinese: https://raw.githubusercontent.com/frePPLe/frepple/master/freppledb/locale/zh-hant/zh-hant.po

  Open the file with the editor you installed in step 1, and start translating. The terms will
  already "pre-translated" with an automated translation engine. Your job as a translator is to
  review the pre-translated strings (marked as "needs work"), change them where needed and remove
  the "needs work" flag. 
  
  Some strings may include HTML tags or Python code, e.g.:

       %(title)s for %(entity)s

  In this case just copy the entire string and translate "for", resulting in:

       %(title)s para %(entity)s

**3. Submit your translation**

  You can submit your translation a) either with a pull request on github, or b) by posting the file to the
  `frePPLe user group <https://groups.google.com/forum/#!forum/frepple-users>`_.

For developers
--------------

**1. Extract all translation strings**

  The translatable strings are present at many places in the source code. A first
  step consist of collecting of these translatable strings in a single file which
  translators can update.

  The following command runs this string collecting.
   
  ::

       make extract-translations

**2. Add support for an additional language**

  Start by copying the translations files of an existing language. You need to copy
  a subdirectory from *freppledb/locale* and 2 files from *freppledb/common/static/common/po*.

  The possible language codes can be found on the `World Wide Web Consortium <http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes>`_.

  You can contact the frepple team and ask them to help you with a pre-translated file. It will makes the
  translation job much easier and faster.
  
  If you want to create installation packages including the new language then the installer also needs
  updating. The files *contrib/installer/parameters.ini* and *contrib/installer/frepple.nsi* need straightforward
  editing.

  To activate it you must also add the new language to *djangosettings.py* (or *bin\\djangosettings.py* in
  the binary Windows installation). Add the new language code and description to the variable LANGUAGES:

  ::

      LANGUAGES = (
        ("en", _("English")),
        ("fr", _("French")),
        ("de", _("German")),
        ("he", _("Hebrew")),
        ("it", _("Italian")),
        ("ja", _("Japanese")),
        ("nl", _("Dutch")),
        ("pt", _("Portuguese")),
        ("pt-br", _("Brazilian Portuguese")),
        ("ru", _("Russian")),
        ("es", _("Spanish")),
        ("zh-hans", _("Simplified Chinese")),
        ("zh-hant", _("Traditional Chinese")),
      )

**3. Let the translators do their work**

  Commit the changes from the previous step, and let the translators bring the
  translation files *freppledb/locale/<LANGUAGE>/<LANGUAGE>.po* up to date.

**4. Compile the translations**

  Run the following command to compile the output of the translators in the
  right format in various data files.
   
  ::

       make compile-translations

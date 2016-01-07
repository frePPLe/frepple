==============================
Translating the user interface
==============================

This section provides step by step instructions on how to translate the user
interface to your favourite language.

.. Hint::

   We are very keen on receiving translations for additional languages. And
   it's an easy way for you to contribute back to the frePPLe community.

#. Edit the file contrib\django\djangosettings.py (or bin\djangosettings.py
   in the binary Windows installation). Add the language code and description
   to the variable LANGUAGES:

   ::

      LANGUAGES = (
        ('en', ugettext('English')),
        ('es', ugettext('Spanish')),
        ('fr', ugettext('French')),
        ('it', ugettext('Italian')),
        ('ja', ugettext('Japanese')),
        ('nl', ugettext('Dutch')),
        ('pt', ugettext('Portuguese')),
        ('pt-br', ugettext('Brazilian Portuguese')),
        ('zh-cn', ugettext('Simplified Chinese')),
        ('zh-tw', ugettext('Traditional Chinese')),
      )

#. Install an editor for gettext catalogs (.po files).

   Highly recommended is the poedit tool, which can be downloaded from
   http://www.poedit.net/

#. Copy the directory contrib\django\freppledb\locale\en to a new subdirectory
   with the name of your language code.

   The possible language codes can be found on
   http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes

#. Use poedit to open the files django.po and djangojs.po in the directories
   you just copied. There are around 500 strings to be translated, which should
   take about half a day's work.

#. You can now test the translations, after a restart of the web server.

   Update your user preferences to use the new language. If your browser has
   the new language as the preferred language, this isn't required.

#. The installer also needs updating to recognize the new language.

   The files contrib\installer\parameters.ini and contrib\installer\frepple.nsi
   need straightforward editing.

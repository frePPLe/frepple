==============================
Translating the user interface
==============================

This section provides step by step instructions on how to translate the user interface to your favourite language.

.. Hint::

   We are very keen on receiving translations for additional languages. And it's an easy way for you to contribute back to the frePPLe community.

**1. Add support for an additional language**

  You may skip this step if you just want to improve already existing translations.

  Copy the directory *freppledb/locale/en* to a new subdirectory with the name of your language code.

  The possible language codes can be found on the `World Wide Web Consortium <http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes>`_.

  If you want to create installation packages including the new language then the installer also needs updating. The files *contrib/installer/parameters.ini* and *contrib/installer/frepple.nsi* need straightforward editing.

  To get it working you must also add the new language to *djangosettings.py* (or *bin\\djangosettings.py* in the binary Windows installation). Add the new language code and description to the variable LANGUAGES:

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

**2. Pick an editor**

  For the translation process you should install an editor for gettext catalogs (.po files).

  Highly recommended is the free `Poedit tool <https://poedit.net/>`_.

**3. Start translating**

   Navigate to *freppledb/locale/* go to the folder with the language you intend to translate, and use your editor to open the *django.po* and *djangojs.po* files.

   In these files you will find all the strings that may be translated.

   .. Hint::

     Some strings may include HTML tags or Python code, i.e.:

       %(title)s for %(entity)s

     In this case just copy the entire string and translate "for", resulting in:

       %(title)s para %(entity)s

**4. Test the translations**

   You can now test the translations, after a restart of the web server.

   Update your user preferences to use the language you translated. If your browser has the language as the preferred language, this isn't required.

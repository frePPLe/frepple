#!/usr/bin/env bash

# Utility script to maintain translations.
#
# The translations process has 3 steps:
# 1) Run "./translations.sh extract" to get all translatable strings from the source code.
# 2) Translate all strings local/<LANGUAGE>/<LANGUAGE>.po file. The real work!
# 3) Run "./translations.sh compile" to merge the translations into the right places.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. venv/bin/activate
django=`python3 -c "import django; import os; print(os.path.dirname(django.__file__))"`

translations_extract () {
  # extract django
  cd "$SCRIPT_DIR/freppledb"
  "$SCRIPT_DIR/frepplectl.py" makemessages --ignore node_modules --no-wrap -a -d django
  "$SCRIPT_DIR/frepplectl.py" makemessages --ignore node_modules "--ignore=*bootstrap.js" "--ignore=*.min.js" --no-wrap -a -d djangojs
  cd -

  # extract angular
  grunt nggettext_extract

  ## Preparation for each language
  for language in $( ls freppledb/locale )
  do
    ## Build a compendium with known translations
    msgcat --use-first $django/conf/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/admin/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/admin/locale/$language/LC_MESSAGES/djangojs.po \
      $django/contrib/admindocs/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/auth/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/contenttypes/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/flatpages/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/gis/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/humanize/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/postgres/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/redirects/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/sessions/locale/$language/LC_MESSAGES/django.po \
      $django/contrib/sites/locale/$language/LC_MESSAGES/django.po \
      | msgattrib --translated --no-fuzzy -o freppledb/locale/$language/djangocompendium.po
    ## Combine all frepple strings coming from django, djangojs and angular
    mv freppledb/locale/$language/$language.po freppledb/locale/$language/$language_old.po
    msgcat --use-first freppledb/locale/$language/LC_MESSAGES/djangojs.po \
      freppledb/locale/$language/LC_MESSAGES/django.po \
      freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').po \
      freppledb/common/static/common/po/template.pot \
      -o freppledb/locale/$language/$language.po
    ## Pick up known translations from the compendium
    msgmerge --silent \
      --compendium freppledb/locale/$language/djangocompendium.po \
      freppledb/locale/$language/$language_old.po \
      freppledb/locale/$language/$language.po \
      -o freppledb/locale/$language/$language.po
    rm freppledb/locale/$language/$language_old.po freppledb/locale/$language/djangocompendium.po
  done
}

translations_compile () {
  ## Preparation for each language
  for language in $( ls freppledb/locale )
  do
    ## Build a compendium with all translated frepple strings
    msgattrib --translated --no-fuzzy \
      freppledb/locale/$language/$language.po \
      -o freppledb/locale/$language/frepplecompendium.po
    ## Update djangojs file from our compendium
    mv freppledb/locale/$language/LC_MESSAGES/djangojs.po \
       freppledb/locale/$language/LC_MESSAGES/djangojs.old.po
    msgmerge --silent --compendium \
      freppledb/locale/$language/frepplecompendium.po \
      freppledb/locale/$language/$language.po \
      freppledb/locale/$language/LC_MESSAGES/djangojs.old.po \
      | msgattrib --no-obsolete --no-fuzzy -o freppledb/locale/$language/LC_MESSAGES/djangojs.po
    rm freppledb/locale/$language/LC_MESSAGES/djangojs.old.po
    ## Update django file from our compendium
    mv freppledb/locale/$language/LC_MESSAGES/django.po \
       freppledb/locale/$language/LC_MESSAGES/django.old.po
    msgmerge --silent --compendium \
      freppledb/locale/$language/frepplecompendium.po \
      freppledb/locale/$language/$language.po \
      freppledb/locale/$language/LC_MESSAGES/django.old.po \
      | msgattrib --no-obsolete --no-fuzzy -o freppledb/locale/$language/LC_MESSAGES/django.po
    rm freppledb/locale/$language/LC_MESSAGES/django.old.po
    ## Update angular file from our compendium
    mv freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').po \
       freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').old.po
    msgmerge --silent --compendium \
      freppledb/locale/$language/frepplecompendium.po \
      freppledb/locale/$language/$language.po \
      freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').old.po \
      | msgattrib --no-obsolete --no-fuzzy -o freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').po
    rm freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').old.po
    rm freppledb/locale/$language/frepplecompendium.po
  done

  # compile angular
  grunt nggettext_compile

  # compile django
  ./frepplectl.py compilemessages
}


if [ "$1" == "extract" ]
then
  translations_extract
  exit 0
elif [ "$1" == "compile" ]
then
  translations_compile
  exit 0
else
  echo "Usage:"
  echo "   translations extract      -> collects all translation strings from the source code"
  echo "   translations compile      -> builds translation strings into a binary format"
  exit 1
fi

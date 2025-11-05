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

translations_extract_vue() {
  # Extract translatable strings from Vue components
  node extract-vue-translations.js
}

translations_extract() {
  # Extract Django strings
  cd "$SCRIPT_DIR/freppledb"
  "$SCRIPT_DIR/frepplectl.py" makemessages --ignore node_modules --no-wrap -a -d django
  "$SCRIPT_DIR/frepplectl.py" makemessages --no-wrap -a -d djangojs \
      "--ignore=node_modules" \
      "--ignore=*jquery*js" \
      "--ignore=*main.js" \
      "--ignore=*frontend*.js" \
      "--ignore=*bootstrap.js" \
      "--ignore=*grid.locale*" \
      "--ignore=*.min.js"
  cd -

  # Extract Vue strings
  translations_extract_vue

  # Extract angular strings
  npx grunt nggettext_extract

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

    ## Combine all strings (Django, JavaScript, Vue, Angular)
    mv freppledb/locale/$language/$language.po freppledb/locale/$language/$language_old.po

    # First collect all Vue POT files
    VUE_POT_FILES=""
    for app in $(find freppledb -name "vue-messages.pot" -path "*/static/*/i18n/*" | sed -E 's|freppledb/([^/]+)/.*|\1|' | sort | uniq)
    do
      VUE_POT_FILES="$VUE_POT_FILES freppledb/$app/static/$app/i18n/vue-messages.pot"
    done

    # Combine with other translations
    msgcat --use-first freppledb/locale/$language/LC_MESSAGES/djangojs.po \
      freppledb/locale/$language/LC_MESSAGES/django.po \
      freppledb/common/static/common/po/$( echo $language | tr _ - | tr '[:upper:]' '[:lower:]').po \
      freppledb/common/static/common/po/template.pot \
      $VUE_POT_FILES \
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

translations_compile_vue() {
  # For each Vue app
  for app in $(find freppledb -name "vue-messages.pot" -path "*/static/*/i18n/*" | sed -E 's|freppledb/([^/]+)/.*|\1|' | sort | uniq)
  do
    echo "Compiling Vue translations for $app app"

    # Create the output directory if it doesn't exist
    mkdir -p "freppledb/$app/static/$app/i18n"

    # For each language
    for language in $( ls freppledb/locale )
    do
      # Format language code for frontend (e.g., 'en_US' → 'en-us')
      frontend_lang=$(echo $language | tr _ - | tr '[:upper:]' '[:lower:]')

      # Create a file with just the message IDs from the POT file
      mkdir -p "freppledb/$app/static/$app/i18n/temp"
      grep -A 1 "msgid" "freppledb/$app/static/$app/i18n/vue-messages.pot" | grep -v "^--$" | grep -v "^msgid \"\"$" > "freppledb/$app/static/$app/i18n/temp/vue-strings.txt"

      # Create a custom PO file that contains only the Vue app strings
      echo 'msgid ""' > "freppledb/$app/static/$app/i18n/temp-$language.po"
      echo 'msgstr ""' >> "freppledb/$app/static/$app/i18n/temp-$language.po"
      echo '"Content-Type: text/plain; charset=UTF-8\n"' >> "freppledb/$app/static/$app/i18n/temp-$language.po"
      echo "" >> "freppledb/$app/static/$app/i18n/temp-$language.po"

      # Extract each string from the main PO file and add it to our custom PO file
      while read -r msgid_line; do
        if [[ "$msgid_line" == msgid* ]]; then
          # Extract the msgid text
          string=$(echo "$msgid_line" | sed 's/msgid "\(.*\)"/\1/')

          # Escape special characters for grep
          escaped_string=$(echo "$string" | sed 's/[\/&]/\\&/g')

          # Find the corresponding msgstr in the main PO file
          msgstr=$(grep -A 1 "msgid \"$escaped_string\"" "freppledb/locale/$language/$language.po" | grep "msgstr" | head -1)

          # If no translation found, use empty msgstr
          if [[ -z "$msgstr" ]]; then
            msgstr="msgstr \"\""
          fi

          # Add to our custom PO file
          echo "msgid \"$string\"" >> "freppledb/$app/static/$app/i18n/temp-$language.po"
          echo "$msgstr" >> "freppledb/$app/static/$app/i18n/temp-$language.po"
          echo "" >> "freppledb/$app/static/$app/i18n/temp-$language.po"
        fi
      done < "freppledb/$app/static/$app/i18n/temp/vue-strings.txt"

      # Convert PO to JSON using a simple node script
      node -e "
        const fs = require('fs');
        const path = require('path');
        const poContent = fs.readFileSync('freppledb/$app/static/$app/i18n/temp-$language.po', 'utf8');
        const translations = {};

        // Simple regex-based parsing for msgid/msgstr pairs
        const regex = /msgid \"(.*?)\"\s+msgstr \"(.*?)\"/gs;
        let match;

        while ((match = regex.exec(poContent)) !== null) {
          if (match[1] && match[1] !== '') {
            // Unescape any escaped quotes
            const key = match[1].replace(/\\\"/g, '\"');
            const value = match[2] ? match[2].replace(/\\\"/g, '\"') : key;
            translations[key] = value;
          }
        }

        // Write JSON file
        fs.writeFileSync(
          'freppledb/$app/frontend/src/i18n/translations/$frontend_lang.json',
          JSON.stringify(translations, null, 2)
        );
      "

      # Clean up temporary files
      rm "freppledb/$app/static/$app/i18n/temp-$language.po"
      rm -rf "freppledb/$app/static/$app/i18n/temp"
    done
  done
}

translations_compile() {
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

  # Compile Vue translations
  translations_compile_vue

  # Compile angular
  npx grunt nggettext_compile

  # Compile django
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

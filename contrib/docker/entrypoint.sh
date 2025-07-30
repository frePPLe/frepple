#!/bin/bash
set -e

# Configure /etc/frepple/djangosettings
sed -i "s/SECRET_KEY.*mzit.*i8b.*6oev96=.*/SECRET_KEY = \"$(mktemp -u XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)\"/g" /etc/frepple/djangosettings.py
params=(-U ${POSTGRES_USER:-frepple})
if [ -n "$POSTGRES_HOST" ]; then
  params+=(-h $POSTGRES_HOST)
fi
if [ -n "$POSTGRES_PORT" ]; then
  params+=(-p $POSTGRES_PORT)
fi

# Djangosettings must be writeable by the web server to support installing&uninstalling apps
chmod g+w /etc/frepple/djangosettings.py

echo "Waiting for the database to be ready"
retries=10
until pg_isready --timeout=1 "${params[@]}" >/dev/null 2>&1
do
  sleep 1
  ((retries=retries-1))
  if [ $retries -eq 0 ]
  then
    echo "Can't connect to PostgreSQL on $POSTGRES_HOST:$POSTGRES_PORT as user ${POSTGRES_USER:-frepple}"
    exit 1
  fi
done

# Create the databases
frepplectl createdatabase --skip-if-exists

# Check if item table exists on the default schema.
# This is needed to figure out if we load the demo datasets
RAW_OUTPUT=$(frepplectl dbshell <<EOF
SELECT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_name = 'item'
);
EOF
)
# Extract just 't' or 'f'
TABLE_EXISTS=$(echo "$RAW_OUTPUT" | sed -n '3p' | xargs)

# Migrate the databases to build the complete database schema
frepplectl migrate --noinput

# Populate the database with initial data, but only on a fresh install.
if [ "$TABLE_EXISTS" = "t" ]; then
	echo "Schema already created. Skipping initial data population."
else
	echo "Populating initial data"
  frepplectl scenario_copy default scenario1 --description="distribution demo"
  frepplectl scenario_copy default scenario2 --description="manufacturing demo"
  frepplectl loaddata --database=scenario1 distribution_demo --verbosity=0
  frepplectl runplan --database=scenario1 --env=fcst,supply --background
  frepplectl loaddata --database=scenario2 manufacturing_demo --verbosity=0
  frepplectl runplan --database=scenario2 --env=fcst,supply --background
fi

# Automatically start the web service if needed
for sc in $FREPPLE_AUTOSTART_WEBSERVICE
do
  echo "Starting web service for scenario $sc in the background"
  frepplectl runwebservice --database=$sc --daemon 
done

# Configure Apache
grep -qxF 'ServerName' /etc/apache2/apache2.conf || echo "ServerName localhost" >> /etc/apache2/apache2.conf
rm -f /usr/local/apache2/logs/httpd.pid

# Allow custom configuration steps to be added
if [[ -d "/etc/frepple/entrypoint.d" ]]; then
  /bin/run-parts --verbose "/etc/frepple/entrypoint.d"
fi

# Start apache web server
echo "Starting web server"
exec apachectl -D FOREGROUND

exit 1
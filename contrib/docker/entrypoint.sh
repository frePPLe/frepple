#!/bin/bash
set -e

# Configure /etc/frepple/djangosettings
params=(-U ${POSTGRES_USER:-frepple})
if [ -n "$POSTGRES_HOST" ]; then
  sed -i "s/\"HOST\": \"\"/\"HOST\": \"${POSTGRES_HOST}\"/g" /etc/frepple/djangosettings.py
  params+=(-h $POSTGRES_HOST)
fi
if [ -n "$POSTGRES_PORT" ]; then
  sed -i "s/\"PORT\": \"\"/\"PORT\": \"${POSTGRES_PORT}\"/g" /etc/frepple/djangosettings.py
  params+=(-p $POSTGRES_PORT)
fi
if [ -n "$POSTGRES_USER" ]; then
  sed -i "s/\"USER\": \"frepple\"/\"USER\": \"${POSTGRES_USER}\"/g" /etc/frepple/djangosettings.py
fi
if [ -n "$POSTGRES_PASSWORD" ]; then
  sed -i "s/\"PASSWORD\": \"frepple\"/\"PASSWORD\": \"${POSTGRES_PASSWORD}\"/g" /etc/frepple/djangosettings.py
fi

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

# Create and migrate the databases
frepplectl createdatabase --skip-if-exists
frepplectl migrate --noinput

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
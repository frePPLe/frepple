#!/bin/bash
set -e

# Configure /etc/frepple/djangosettings
if [ -n "$POSTGRES_HOST" ]; then
  sed -i "s/\"HOST\": \"\"/\"HOST\": \"${POSTGRES_HOST}\"/g" /etc/frepple/djangosettings.py
fi
if [ -n "$POSTGRES_PORT" ]; then
  sed -i "s/\"PORT\": \"\"/\"PORT\": \"${POSTGRES_PORT}\"/g" /etc/frepple/djangosettings.py
fi
if [ -n "$POSTGRES_USER" ]; then
  sed -i "s/\"USER\": \"frepple\"/\"USER\": \"${POSTGRES_USER}\"/g" /etc/frepple/djangosettings.py
fi
if [ -n "$POSTGRES_PASSWORD" ]; then
  sed -i "s/\"PASSWORD\": \"frepple\"/\"PASSWORD\": \"${POSTGRES_PASSWORD}\"/g" /etc/frepple/djangosettings.py
fi

# TODO check the connection to the database before continuing. Misconfigurations will be the most common error.

# Create and migrate the databases
frepplectl createdatabase --skip-if-exists
frepplectl migrate --noinput

# Configure Apache
grep -qxF 'ServerName' /etc/apache2/apache2.conf || echo "ServerName localhost" >> /etc/apache2/apache2.conf
rm -f /usr/local/apache2/logs/httpd.pid

# Allow custom configuration steps to be added
if [[ -d "/etc/frepple/entrypoint.d" ]]; then
  /bin/run-parts --verbose "/et/frepple/entrypoint.d"
fi

# Start apache web server
echo "Starting web server"
exec apachectl -D FOREGROUND

exit 1
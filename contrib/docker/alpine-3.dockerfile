#
# Copyright (C) 2020 by frePPLe bv
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# STAGE 1: Compile and build the application
#

FROM alpine:3.12 as builder

RUN apk add --update --no-cache --virtual .build-deps \
  xerces-c xerces-c-dev apache2 apache2-mod-wsgi \
  python3-dev py3-pip py3-psycopg2 py3-lxml postgresql postgresql-dev \
  libpq openssl openssl-dev libxml2 py3-sphinx \
  cmake g++ git wget

# An alternative to the copy is to clone from git:
# RUN git clone https://github.com/frepple/frepple.git frepple
COPY frepple-*.tar.gz ./

RUN src=`basename --suffix=.tar.gz frepple-*` && \
  tar -xzf *.tar.gz && \
  rm *.tar.gz && \
  cd $src && \
  sed -i '/lxml/d' requirements.txt && \
  python3 -m pip install -r requirements.txt && \
  mkdir build && \
  cd build && \
  cmake .. && \
  cmake --build . --target package
    
FROM scratch as package
COPY --from=builder frepple-*/build/*.deb .

#
# STAGE 2: Build the deployment container
#

FROM alpine:3.12

RUN apk add --update --no-cache --virtual .build-deps \
  xerces-c apache2 apache2-mod-wsgi \
  py3-pip py3-psycopg2 py3-lxml postgresql-client \
  openssl libxml2 && \
  rm -rf .build-deps

COPY --from=builder /requirements.txt /
COPY --from=builder /frepple_install_files.tgz /

RUN tar xvfz frepple_install_files.tgz && \
  pip3 install -r requirements.txt && \
  rm /requirements.txt /frepple_install_files.tgz
#  a2enmod expires && \
#  a2enmod wsgi && \
#  a2enmod ssl && \
#  a2ensite default-ssl && \
#  a2ensite frepple && \
#  a2enmod proxy && \
#  a2enmod proxy_wstunnel && \
#  service apache2 restart && \

EXPOSE 80
EXPOSE 443

# Update djangosettings
# TODO update random secret key
RUN sed -i 's/"HOST": ""/"HOST": "frepple-postgres"/g' /etc/frepple/djangosettings.py

VOLUME ["/var/log/frepple", "/etc/frepple", "/var/log/apache2", "/etc/apache2"]

CMD frepplectl migrate && \
  rm -f /usr/local/apache2/logs/httpd.pid && \
  apachectl -DFOREGROUND

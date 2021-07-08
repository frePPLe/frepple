#
# Copyright (C) 2018-2019 by frePPLe bv
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

FROM ubuntu:18.04 as builder

RUN apt-get -y -q update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
  cmake g++ git python3 python3-pip python3-dev python3-psycopg2 python3-sphinx \
  libxerces-c3.2 libxerces-c-dev openssl libssl-dev libpq5 libpq-dev python3-lxml

# An alternative to the copy is to clone from git:
# RUN git clone https://github.com/frepple/frepple.git frepple
COPY frepple-*.tar.gz ./

RUN src=`basename --suffix=.tar.gz frepple-*` && \
  tar -xzf *.tar.gz && \
  rm *.tar.gz && \
  cd $src && \
  python3 -m pip install --upgrade pip && \
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

FROM ubuntu:18.04

RUN apt-get -y -q update && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
  libxerces-c3.2 apache2 libapache2-mod-wsgi-py3 \
  python3-psycopg2 python3-pip postgresql-client \
  libpq5 openssl python3-lxml libapache2-mod-xsendfile ssl-cert python3-setuptools python3-wheel build-essential python3-dev

#COPY --from=builder /requirements.txt /
COPY requirements.txt ./
COPY *.deb /

RUN dpkg -i *.deb && \
  apt-get -f -y -q install && \
  python3 -m pip install --upgrade pip && \
  pip3 install -r requirements.txt && \
  a2enmod expires && \
  a2enmod wsgi && \
  a2enmod ssl && \
  a2ensite default-ssl && \
  a2ensite z_frepple && \
  a2enmod proxy && \
  a2enmod proxy_wstunnel && \
  service apache2 restart && \
  rm requirements.txt *.deb && \
  apt-get -y purge --autoremove build-essential python3-dev && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

EXPOSE 80
EXPOSE 443

# Update djangosettings
# TODO update random secret key
RUN sed -i 's/"HOST": ""/"HOST": "frepple-postgres"/g' /etc/frepple/djangosettings.py

VOLUME ["/var/log/frepple", "/etc/frepple", "/var/log/apache2", "/etc/apache2"]

CMD frepplectl migrate && \
  rm -f /usr/local/apache2/logs/httpd.pid && \
  apachectl -DFOREGROUND

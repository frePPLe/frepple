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

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get -y -q update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
  cmake g++ git python3 python3-pip python3-dev python3-psycopg2 \
  libxerces-c3.2 libxerces-c-dev python3-lxml \
  openssl libssl-dev libpq5 libpq-dev locales

COPY requirements.dev.txt /
COPY requirements.txt /

RUN python3 -m pip install --upgrade pip && \
  python3 -m pip install -r requirements.dev.txt

# An alternative to the copy would be to clone or download from github
COPY frepple-*.tar.gz ./

RUN src=`basename --suffix=.tar.gz frepple-*` && \
  tar -xzf *.tar.gz && \
  rm *.tar.gz *.txt && \
  mkdir "$src/build" && \
  cd "$src/build" && \
  cmake .. && \
  cmake --build . --target package -- -j 2

FROM scratch as package
COPY --from=builder frepple-*/build/*.deb .

#
# STAGE 2: Build the deployment container
#

FROM ubuntu:18.04

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends curl ca-certificates gnupg && \
  curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
  echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
  apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
  libxerces-c3.2 apache2 libapache2-mod-wsgi-py3 python3-pip postgresql-client-13 \
  python3-setuptools python3-wheel build-essential python3-dev python3-psycopg2 \
  libpq5 openssl python3-lxml libapache2-mod-xsendfile ssl-cert locales

COPY requirements.txt /

RUN python3 -m pip install --upgrade pip && \
  python3 -m pip install -r requirements.txt && \
  rm requirements.txt

COPY --from=builder frepple-*/build/*.deb .

RUN dpkg -i *.deb && \
  apt-get -f -y -q install && \
  a2enmod expires && \
  a2enmod wsgi && \
  a2ensite z_frepple && \
  a2enmod proxy && \
  a2enmod proxy_wstunnel && \
  apt-get -y purge --autoremove build-essential python3-dev && \
  apt-get clean && \
  rm -rf *.deb /var/lib/apt/lists/* /etc/apt/sources.list.d/pgdg.list

EXPOSE 80

# Use the following lines to enable HTTPS. 
# Inherit from this base image, add the following lines in your dockerfile
# and copy your certificate files into the image.
# RUN a2enmod ssl && \
#   a2ensite default-ssl && \
# EXPOSE 443

VOLUME ["/var/log/frepple", "/etc/frepple", "/var/log/apache2", "/etc/apache2"]

COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

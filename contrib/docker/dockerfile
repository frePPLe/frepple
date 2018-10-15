#
# Copyright (C) 2018 by frePPLe bvba
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

FROM ubuntu:16.04 as builder
RUN apt-get -y -q update && apt-get -y install \
  libxerces-c3.1 apache2 libapache2-mod-wsgi-py3 \
  python3-psycopg2 python3-pip postgresql-client

RUN apt-get -y install git wget libtool \
  make python3-dev libxerces-c-dev automake autoconf g++ \
  python-sphinx cdbs debhelper pbuilder python3-sphinx 

# A trick to force rebuilding from here if there are new commits
ADD https://api.github.com/repos/frePPLe/frepple/compare/master...HEAD /dev/null
RUN git clone https://github.com/frePPLe/frepple.git frepple && \
  pip3 install -r frepple/requirements.txt

WORKDIR /frepple
RUN make -f Makefile.dist prep config && \
  cd contrib/debian && \
  make contrib

#
# STAGE 2: Build the deployment container
#

FROM ubuntu:16.04

RUN apt-get -y -q update && apt-get -y install \
  libxerces-c3.1 apache2 libapache2-mod-wsgi-py3 \
  python3-psycopg2 python3-pip postgresql-client

# The following copy commands don't work on LCOW:
# See https://github.com/moby/moby/issues/33850
COPY --from=builder /frepple/requirements.txt .
COPY --from=builder /frepple/contrib/debian/frepple_*.deb .

RUN dpkg -i frepple_*.deb && \
  apt-get -f -y -q install && \
  pip3 install -r requirements.txt && \
  a2enmod expires && \
  a2enmod wsgi && \
  a2enmod ssl && \
  a2ensite default-ssl && \
  a2ensite frepple && \
  service apache2 restart && \
  rm requirements.txt *.deb

EXPOSE 80
EXPOSE 443

CMD frepplectl migrate && \
  rm -f /usr/local/apache2/logs/httpd.pid && \
  apachectl -DFOREGROUND

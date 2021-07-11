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

FROM debian:10-slim as builder

RUN apt-get -y -q update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
  libxerces-c3.2 apache2 libapache2-mod-wsgi-py3 \
  python3-psycopg2 python3-pip postgresql \
  git cmake g++ python3-dev libxerces-c-dev \
  python3-sphinx \
  openssl libssl-dev libpq-dev python3-lxml

# OPTION 1: BUILDING FROM LOCAL DISTRIBUTION:
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip && pip3 install -r requirements.txt 

COPY *.tar.gz ./
COPY debian/  debian/

# subtle - and _ things going on here...
RUN sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /etc/postgresql/11/main/pg_hba.conf && \
  /etc/init.d/postgresql start && \
  sudo -u postgres psql template1 -c "create role frepple login superuser password 'frepple'" && \
  tar -xzf *.orig.tar.gz && \
  src=`basename --suffix=.orig.tar.gz frepple-*` && \
  mv debian $src && \
  cd $src && \
  mkdir logs && \
  dpkg-buildpackage -us -uc -D

# OPTION 2: BUILDING FROM GIT REPOSITORY
# This is useful when using this dockerfile standalone.
# A trick to force rebuilding from here if there are new commits
#ADD https://api.github.com/repos/jdetaeye/frepple-enterprise/compare/master...HEAD /dev/null
#RUN git clone https://github.com/jdetaeye/frepple-enterprise.git frepple && \
#  pip3 install -r frepple/requirements.txt
# TODO build from git repo

FROM scratch as package
COPY --from=builder frepple-*/build/*.deb .

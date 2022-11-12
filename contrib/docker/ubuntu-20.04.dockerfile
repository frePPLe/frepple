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

FROM ubuntu:20.04 as builder

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install \
  cmake g++ git python3 python3-pip python3-dev python3-venv \
  psmisc libxerces-c3.2 libxerces-c-dev openssl libssl-dev \
  postgresql-client libpq5 libpq-dev locales && \
  rm -rf /var/lib/apt/lists/*

# An alternative to the copy is to clone from git:
# RUN git clone https://github.com/frepple/frepple.git frepple
COPY frepple-*.tar.gz ./

RUN src=`basename --suffix=.tar.gz frepple-*` && \
  tar -xzf *.tar.gz && \
  rm *.tar.gz && \
  cd $src && \
  python3 -m pip install --upgrade pip && \
  python3 -m pip install -r requirements.dev.txt && \
  cmake -B /build -DCMAKE_BUILD_TYPE=Release && \
  cmake --build /build --config Release --target package -- -j 2

FROM scratch as package
COPY --from=builder /build/*.deb .

#
# STAGE 2: Build the deployment container
#

FROM ubuntu:20.04

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends curl ca-certificates gnupg && \
  curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
  echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
  apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install postgresql-client-15

COPY --from=builder /build/*.deb .

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install --no-install-recommends -f -y -q ./*.deb && \
  apt-get -y purge --autoremove && \
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

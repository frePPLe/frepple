#
# Copyright (C) 2019 by frePPLe bv
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

FROM roboxes/rhel8 as builder

# REQUIRED BUILD ARGUMENTS!
# Credentials for access to the rhel repositories
ARG RHEL_USER
ARG RHEL_PASSWORD

RUN subscription-manager register --username $RHEL_USER --password $RHEL_PASSWORD --auto-attach && \
  yum -y update && \
  yum -y install epel-release && \
  yum -y install xerces-c python36 rpm-build rpm-sign git wget \
  python3-psycopg2 python3-pip postgresql-devel openssl openssl-devel \
  libtool make python3-devel xerces-c-devel automake autoconf gcc-c++ && \
  yum clean all 
RUN subscription-manager unregister

RUN useradd builder -u 6666 -m -G users && \
  echo "builder ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers && \
  echo "%_topdir    /home/builder/rpm" > /home/builder/.rpmmacros && \
  echo "%_gpg_name  devops@frepple.com" >> /home/builder/.rpmmacros && \
  mkdir /home/builder/rpm && \
  mkdir -p /home/builder/rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
  chown -R builder /home/builder

# OPTION 1: BUILDING FROM LOCAL DISTRIBUTION:
ADD requirements.txt gpg_key* ./
USER builder
RUN pip3 install --user -r requirements.txt sphinx

# An alternative to the copy is to clone from git:
# RUN git clone https://github.com/frepple/frepple.git frepple
COPY --chown=6666 frepple.spec /home/builder/rpm/SPECS/
COPY --chown=6666 *.tar.gz /home/builder/rpm/SOURCES/
RUN rpmbuild -ba /home/builder/rpm/SPECS/frepple.spec

# Optional: sign the rpm file
RUN if test -f gpg_key; \
  then \
  gpg --import gpg_key; \
  rpm --addsign /home/builder/rpm/RPMS/x86_64/*.rpm; \
  fi

FROM scratch as package
COPY --from=builder frepple-*/build/*.rpm .

#
# STAGE 2: Build the deployment container
#

FROM roboxes/rhel8

COPY --from=builder /frepple/requirements.txt .
COPY --from=builder /frepple/contrib/centos/frepple_*.rpm .

RUN subscription-manager register --username $RHEL_USER --password $RHEL_PASSWORD --auto-attach && \
  yum -y update && \
  yum -y install xerces-c python36 httpd python3-mod_wsgi \
  python3-psycopg2 python3-pip openssl postgresql-client && \
  yum clean all && \
  subscription-manager unregister

RUN yum -y --no-install-recommends install \
  libxerces-c3.2 apache2 libapache2-mod-wsgi-py3 \
  python3-wheel ssl-cert python3-setuptools python3-psycopg2 python3-pip postgresql-client && \
  rpm -i frepple_*.rpm && \
  pip3 install -r requirements.txt && \
  a2enmod expires && \
  a2enmod wsgi && \
  a2enmod ssl && \
  a2ensite default-ssl && \
  a2ensite z_frepple && \
  service apache2 restart && \
  rm requirements.txt *.rpm && \
  yum -y remove python3-wheel python3-setuptools python3-pip

EXPOSE 80
EXPOSE 443

VOLUME ["/var/log/frepple", "/etc/frepple", "/var/log/apache2", "/etc/apache2"]

# Update djangosettings
# TODO update random secret key
RUN sed -i 's/"HOST": ""/"HOST": "frepple-postgres"/g' /etc/frepple/djangosettings.py

CMD frepplectl migrate && \
  rm -f /usr/local/apache2/logs/httpd.pid && \
  apachectl -DFOREGROUND

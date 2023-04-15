#
# Copyright (C) 2019 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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
  python3-pip postgresql-devel openssl openssl-devel \
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
RUN pip3 install --user -r requirements.txt

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

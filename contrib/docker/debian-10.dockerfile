#
# Copyright (C) 2020 by frePPLe bv
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

FROM debian:10-slim as builder

RUN apt -y -q update && DEBIAN_FRONTEND=noninteractive apt -y install \
  libxerces-c3.2 apache2 libapache2-mod-wsgi-py3 \
  python3-pip postgresql \
  git cmake g++ python3-dev libxerces-c-dev \
  openssl libssl-dev libpq-dev

# OPTION 1: BUILDING FROM LOCAL DISTRIBUTION:
COPY *.tar.gz ./

# subtle - and _ things going on here...
RUN sed -i 's/local\(\s*\)all\(\s*\)all\(\s*\)peer/local\1all\2all\3\md5/g' /etc/postgresql/11/main/pg_hba.conf && \
  /etc/init.d/postgresql start && \
  sudo -u postgres psql template1 -c "create role frepple login superuser password 'frepple'" && \
  tar -xzf *.orig.tar.gz && \
  src=`basename --suffix=.orig.tar.gz frepple-*` && \
  cd $src && \
  mkdir logs && \
  dpkg-buildpackage -us -uc -D

# OPTION 2: BUILDING FROM GIT REPOSITORY
# This is useful when using this dockerfile standalone.
# A trick to force rebuilding from here if there are new commits
#ADD https://api.github.com/repos/frepple/frepple/compare/master...HEAD /dev/null
#RUN git clone https://github.com/frepple/frepple.git frepple && \
#  pip3 install -r frepple/requirements.txt
# TODO build from git repo

FROM scratch as package
COPY --from=builder frepple-*/build/*.deb .

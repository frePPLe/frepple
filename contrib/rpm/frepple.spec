#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision: 105 $  $LastChangedBy$
# date : $LastChangedDate$

Summary: Free Production Planning Library
Name: frepple
Version: 0.7.1.beta
Release: 1
License: GLPL
Group: Office/Productivity
Source: frepple-%{version}.tar.gz
URL: http://frepple.sourceforge.net
Buildroot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-XXXXXX)
Requires: python xerces-c
# @todo add django dependency
BuildRequires: doxygen python-devel xerces-c-devel
Prefix: /usr

%description
FrePPLe stands for "Free Production Planning Library". It aims at building a
toolkit for modeling and solving production planning problems, targetted
primarily at discrete manufacturing industries.

%package devel
Summary: Development headers for frePPLe - the Free Production Planning Library
Group: Office/Productivity
Requires: frepple

%description devel
These are the develop headers for frePPLe.

%prep
%setup -q

%build
./configure \
  --disable-rpath \
  --disable-dependency-tracking \
  --enable-doc \
  --enable-forecast \
  --disable-lp_solver \
  --disable-webservice \
  --prefix=%{prefix} \
  --docdir=%{buildroot}%{_prefix}/share/doc/frepple-%{version} \
  --datadir=%{prefix}/share/frepple
make all

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%clean
rm -rf %{buildroot}

%post
/sbin/ldconfig
echo Finished installation of frePPLe

# @todo configure django in web server

%postun
/sbin/ldconfig

%files
%defattr(-,root,root)
%{prefix}/bin/frepple
%{prefix}/lib/frepple/mod_forecast.so
#%{prefix}/lib/frepple/mod_lp_solver.so
#%{prefix}/lib/frepple/mod_webservice.so
#%{prefix}/lib/libfrepple.la
%{prefix}/lib/libfrepple.so
%{prefix}/lib/libfrepple.so.0
%{prefix}/lib/libfrepple.so.0.0.0
#%{prefix}/lib/mod_forecast.la
%{prefix}/share/frepple/mod_forecast.xsd
#%{prefix}/share/frepple/mod_lpsolver.xsd
#%{prefix}/share/frepple/mod_webservice.xsd
%{prefix}/share/frepple/frepple.xsd
%{prefix}/share/frepple/frepple_core.xsd
%{prefix}/share/frepple/init.xml
%{prefix}/share/man/man1/frepple.1.gz
%doc COPYING doc/reference doc/*.pdf doc/favicon.ico doc/*.html doc/*.css doc/*.gif doc/*.bmp

%files devel
%dir %{prefix}/include/frepple
%{prefix}/include/frepple/*
%{prefix}/include/frepple.h
%{prefix}/include/freppleinterface.h
%{prefix}/*/*.la
%{prefix}/*/*/*.la




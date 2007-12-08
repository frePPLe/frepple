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

Summary: FREE Production Planning Library
Name: frepple
Version: 0.4.0-beta
Release: 1
License: GLPL
Group: Office/Productivity
Source: frepple-%{version}.tar.gz
URL: http://frepple.sourceforge.net
Vendor: jdetaeye@users.sourceforge.net
Packager: Johan De Taeye <jdetaeye@users.sourceforge.net>
Buildroot: /tmp/frepple
Prefix: /usr

%description
Frepple stands for "FREE Production Planning Library". It aims at building a
toolkit for modeling and solving production planning problems, targetted at
discrete manufacturing industries.

%prep
%setup -q

%build
./configure --enable-doc --prefix=%{buildroot}%{prefix} --docdir=%{buildroot}%{prefix}/share/doc/frepple
make all

%install
make install

%clean
rm -rf %{buildroot}

%post
/sbin/ldconfig
echo Finished installation of frepple

%postun
/sbin/ldconfig

%files
%defattr(-,root,root)
%{prefix}/bin/frepple
%{prefix}/bin/frepple_static
%{prefix}/lib/libfrepple*
%{prefix}/lib/libforecast*
%dir %{prefix}/include/frepple
%{prefix}/include/frepple/*
%{prefix}/include/tags.h
%{prefix}/include/frepple.h
%{prefix}/include/freppleinterface.h
%doc doc/* COPYING

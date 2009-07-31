#
# Copyright (C) 2007-2009 by Johan De Taeye
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

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Free Production Planning Library
Name: frepple
Version: 0.7.1
Release: 1%{?dist}
# Note on the license: frePPle is released with the LGPL license. 
# The optional plugin module mod_lpsolver depends on the GLPK package which is 
# licensed under GPL. That module is therefore disabled in this build.
License: LGPL, v2.1 or greater
Group: Applications/Productivity
Source: http://downloads.sourceforge.net/sourceforge/frepple/%{name}-%{version}.tar.gz
Source1: %{name}-%{version}.tar.gz
URL: http://www.frepple.com
Buildroot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-XXXXXX)
Requires: python, xerces-c
BuildRequires: doxygen, python-devel, xerces-c-devel, automake, autoconf, libtool, django

%description
FrePPLe stands for "Free Production Planning Library". It is a toolkit/
framework for modeling and solving production planning problems, targeted
primarily at discrete manufacturing industries.

%package devel
Summary: The libraries and header files needed for frePPLe development.
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description devel
These are the libraries and header files need for developing plug-ins and
extensions of frePPLe - the Free Production Planning Library.

%prep
%setup -q

%build
# Configure
%configure \
  --disable-static \
  --disable-dependency-tracking \
  --enable-doc \
  --enable-forecast \
  --disable-lp_solver \
  --disable-webservice 
# Remove rpath from libtool
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
# Compile
make all

%check
# Run test suite
make check

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} 
# Do not package .la files created by libtool
find %{buildroot} -name '*.la' -exec rm {} \;
# Use %doc instead of install to create the documentation
rm -rf %{buildroot}%{_docdir}/%{name}

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
%{_bindir}/frepple
%dir %{_libdir}/frepple
%{_libdir}/frepple/mod_forecast.so
%{_libdir}/libfrepple.so.0
%{_libdir}/libfrepple.so.0.0.0
%dir %{_datadir}/frepple
%{_datadir}/frepple/*.xsd
%{_datadir}/frepple/*.xml
%{_datadir}/frepple/*.py*
%{_mandir}/man1/frepple.1.gz
%{python_sitelib}
%doc COPYING doc/reference doc/*.pdf doc/favicon.ico doc/*.html doc/*.css doc/*.gif doc/*.bmp

%files devel
%defattr(-,root,root)
%{_libdir}/libfrepple.so
%dir %{_includedir}/frepple
%{_includedir}/frepple/*
%{_includedir}/frepple.h
%{_includedir}/freppleinterface.h

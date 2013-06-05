#
# Copyright (C) 2007-2012 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Free Production PLanning
Name: frepple
Version: 2.1.beta
Release: 1%{?dist}
# Note on the license: frePPle is released with the AGPL license, version 3 or higher. 
# The optional plugin module mod_lpsolver depends on the GLPK package which is 
# licensed under GPL. That module is therefore disabled in this build.
License: AGPLv3+
Group: Applications/Productivity
URL: http://www.frepple.com
Source: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-XXXXXX)
Requires: xerces-c, Django
BuildRequires: python-devel, xerces-c-devel

%description
FrePPLe stands for "Free Production PLanning". It is an application for
modeling and solving production planning problems, targeted primarily
at discrete manufacturing industries.

%package devel
Summary: The libraries and header files needed for frePPLe development
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}

%description devel
These are the libraries and header files need for developing plug-ins and
extensions of frePPLe - free Production PLanning.

%package doc
Summary: Documentation subpackage for frePPLe
Group: Documentation
Requires: %{name} = %{version}-%{release}
%if 0%{?fedora} || 0%{?rhel} > 5
BuildArch: noarch
%endif

%description doc
Documentation subpackage for frePPLe - free Production PLanning.

%prep
%setup -q

%build
# Configure
%configure \
  --disable-static \
  --disable-dependency-tracking \
  --disable-doc \
  --disable-lp_solver
# Remove rpath from libtool
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
# Avoid linking against unused libraries
sed -i -e 's| -shared | -Wl,--as-needed\0|g' libtool
# Compile
make %{?_smp_mflags} all

%check
# Run test suite, skipping some long and less interesting tests
TESTARGS="--regression -e setup_1 -e setup_2 -e setup_3 -e operation_routing -e constraints_combined_1"
export TESTARGS
make check

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} 
# Do not package .la files created by libtool
find %{buildroot} -name '*.la' -exec rm {} \;
# Use percent-doc instead of install to create the documentation
rm -rf %{buildroot}%{_docdir}/%{name}
# Language files; not under /usr/share, need to be handled manually
(cd $RPM_BUILD_ROOT && find . -name 'django*.mo') | %{__sed} -e 's|^.||' | %{__sed} -e \
  's:\(.*/locale/\)\([^/_]\+\)\(.*\.mo$\):%lang(\2) \1\2\3:' \
  >> %{name}.lang

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files -f %{name}.lang
%defattr(-,root,root,-)
%{_bindir}/frepple
%{_bindir}/manage.py
%dir %{_libdir}/frepple
%{_libdir}/frepple/libfrepple.so.0
%{_libdir}/frepple/libfrepple.so.0.0.0
%dir %{_datadir}/frepple
%{_datadir}/frepple/*.xsd
%{_datadir}/frepple/*.xml
%{_mandir}/man1/frepple.1.*
%{python_sitelib}/freppledb*
%doc COPYING 

%files devel
%defattr(-,root,root,-)
%{_libdir}/frepple/libfrepple.so
%dir %{_includedir}/frepple
%{_includedir}/frepple/*
%{_includedir}/frepple.h
%{_includedir}/freppleinterface.h

%files doc
%defattr(-,root,root,-)
%doc doc/html


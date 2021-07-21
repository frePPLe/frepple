
if (CMAKE_SYSTEM_NAME MATCHES "Linux")

# Debian style packaging
set(CPACK_DEBIAN_PACKAGE_SOURCE "frePPLe")
set(CPACK_DEBIAN_PACKAGE_SECTION "science")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "frePPLe team <info@frepple.com>")
set(CPACK_DEBIAN_PACKAGE_HOMEPAGE "https://frepple.com")
set(CPACK_DEBIAN_PACKAGE_CONTROL_STRICT_PERMISSION TRUE)
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
  "${CMAKE_CURRENT_SOURCE_DIR}/postrm"
  "${CMAKE_CURRENT_SOURCE_DIR}/postinst"
  "${CMAKE_CURRENT_SOURCE_DIR}/conffiles"
   )
set(CPACK_DEBIAN_PACKAGE_DEPENDS 
  "adduser, libxerces-c3.2 | libxerces-c3.1, apache2, libapache2-mod-wsgi-py3, libapache2-mod-xsendfile, python3-psycopg2, postgresql-client"
  )

# RPM style packaging
if (DISTRO STREQUAL "opensuse15")
  set(CPACK_RPM_PACKAGE_REQUIRES "libxerces-c-3_1, httpd, apache2-mod_wsgi-python3, python3, python3-psycopg2, gcc, python3-devel")
else()
  set(CPACK_RPM_PACKAGE_REQUIRES "xerces-c, httpd, python3-mod_wsgi, mod_xsendfile, python3, python3-psycopg2, postgresql-client")
  set(CPACK_RPM_PACKAGE_REQUIRES_POST "shadow-utils")
endif()
set(CPACK_RPM_PRE_INSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/rpm_pre_install")
set(CPACK_RPM_POST_INSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/rpm_post_install")
set(CPACK_RPM_POST_UNINSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/rpm_post_uninstall")

# Build package
set(CPACK_PACKAGE_FILE_NAME "${DISTRO}-${PROJECT_NAME}-${CPACK_PACKAGE_VERSION}")
set(CPACK_PACKAGING_INSTALL_PREFIX "/")
set(CPACK_SOURCE_GENERATOR "TGZ")
if (CPACK_GENERATOR STREQUAL "RPM")
  install(
    FILES httpd.conf
    RENAME "z_frepple.conf"
    DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/httpd/sites-available"
    )
elseif (CPACK_GENERATOR STREQUAL "DEB")
  install(
    FILES httpd.conf
    RENAME "z_frepple.conf"
    DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/apache2/sites-available"
    )
endif()
include(CPack)

endif (CMAKE_SYSTEM_NAME MATCHES "Linux")

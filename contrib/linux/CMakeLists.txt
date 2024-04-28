
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/preinst"
    "${CMAKE_CURRENT_BINARY_DIR}/preinst"
    @ONLY
  )
  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/httpd.conf"
    "${CMAKE_CURRENT_BINARY_DIR}/httpd.conf"
    @ONLY
  )
  # Debian style packaging
  set(CPACK_DEBIAN_PACKAGE_SOURCE "frePPLe")
  set(CPACK_DEBIAN_PACKAGE_SECTION "science")
  set(CPACK_DEBIAN_PACKAGE_MAINTAINER "frePPLe team <info@frepple.com>")
  set(CPACK_DEBIAN_PACKAGE_HOMEPAGE "https://frepple.com")
  set(CPACK_DEBIAN_PACKAGE_CONTROL_STRICT_PERMISSION TRUE)
  set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
    "${CMAKE_CURRENT_SOURCE_DIR}/postrm"
    "${CMAKE_CURRENT_BINARY_DIR}/preinst"
    "${CMAKE_CURRENT_SOURCE_DIR}/postinst"
    "${CMAKE_CURRENT_SOURCE_DIR}/conffiles"
    "${CMAKE_CURRENT_SOURCE_DIR}/templates"
    "${CMAKE_CURRENT_SOURCE_DIR}/config"
  )
  set(CPACK_DEBIAN_PACKAGE_DEPENDS
    "adduser, libxerces-c3.2 | libxerces-c3.1, apache2, libapache2-mod-wsgi-py3, libapache2-mod-xsendfile, postgresql-client-16 | postgresql-client-15 | postgresql-client-14 | postgresql-client, psmisc, locales, libpq5, openssl, ssl-cert")

  # Build package
  set(CPACK_PACKAGE_FILE_NAME "${DISTRO}-${PROJECT_NAME}-${CPACK_PACKAGE_VERSION}")
  set(CPACK_PACKAGING_INSTALL_PREFIX "/")
  set(CPACK_SOURCE_GENERATOR "TGZ")

  if(CPACK_GENERATOR STREQUAL "DEB")
    install(
      FILES "${CMAKE_CURRENT_BINARY_DIR}/httpd.conf"
      RENAME "z_frepple.conf"
      DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/apache2/sites-available"
    )
  endif()

  include(CPack)
endif(CMAKE_SYSTEM_NAME MATCHES "Linux")


INSTALL(
  FILES frepple.1 frepplectl.1
  DESTINATION "${CMAKE_INSTALL_MANDIR}"
)

add_custom_target(
  doc
  DEPENDS venv
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_CURRENT_BINARY_DIR}/_build
  COMMAND "${Python3_VENV}/sphinx-build" -a -E -b html
  -d ${CMAKE_CURRENT_BINARY_DIR}/_build/doctrees
  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}/_build/html
  -D "version=current" -D "release=${PROJECT_VERSION}"
  -D "html_baseurl=https://your-site.com/docs/"
  COMMAND tar "cf" "${CMAKE_BINARY_DIR}/frepple-doc-${PROJECT_VERSION}.tgz" -C ${CMAKE_CURRENT_BINARY_DIR}/_build -- html
)

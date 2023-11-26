
if(NOT WIN32)
  INSTALL(
    FILES frepple.1 frepplectl.1
    DESTINATION "${CMAKE_INSTALL_MANDIR}"
  )
  set(sphinxbuild "${PROJECT_SOURCE_DIR}/venv/bin/sphinx-build")
else()
  set(sphinxbuild "${PROJECT_SOURCE_DIR}/venv/Scripts/sphinx-build")
endif()

add_custom_target(
  doc
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_CURRENT_BINARY_DIR}/_build
  COMMAND ${sphinxbuild} -a -E -b html
  -d ${CMAKE_CURRENT_BINARY_DIR}/_build/doctrees
  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}/_build/html
  -D "version=current" -D "release=${PROJECT_VERSION}"
  -D "html_baseurl=https://your-site.com/docs/"
  COMMAND tar "cf" "${CMAKE_BINARY_DIR}/frepple-doc-${PROJECT_VERSION}.tgz" -C ${CMAKE_CURRENT_BINARY_DIR}/_build -- html
)

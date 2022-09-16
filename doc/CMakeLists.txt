
find_program(sphinxbuild NAMES sphinx-build sphinx-build-3)

if(sphinxbuild)
  add_custom_target(
    doc
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_CURRENT_BINARY_DIR}/_build
    COMMAND ${sphinxbuild} -a -E -b html
    -d ${CMAKE_CURRENT_BINARY_DIR}/_build/doctrees
    ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}/_build/html
    -D "version=${PROJECT_VERSION}" -D "release=${PROJECT_VERSION}"
    COMMAND tar "cf" "${CMAKE_BINARY_DIR}/frepple-doc-${PROJECT_VERSION}.tgz" -C ${CMAKE_CURRENT_BINARY_DIR}/_build -- html
  )
else()
  message("No documentation can be built - missing sphinx-build")
endif()

if(NOT WIN32)
  INSTALL(
    FILES frepple.1 frepplectl.1
    DESTINATION "${CMAKE_INSTALL_MANDIR}"
  )
endif()


if (WIN32)

find_program(NSIS_EXECUTABLE makensis
  HINTS "/Program Files (x86)/NSIS"
  )

if (NSIS_EXECUTABLE)
  file(TO_NATIVE_PATH "${CMAKE_BINARY_DIR}" CMAKE_BINARY_DIR_NATIVE)
  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/settings.nsi.in"
    "${CMAKE_CURRENT_BINARY_DIR}/settings.nsi"
    )
  add_custom_target(
    installer
    COMMAND "${PYTHON_EXECUTABLE}" setup.py build --quiet --build-base "${CMAKE_CURRENT_BINARY_DIR}" "--version=${PROJECT_VERSION}"
    COMMAND "${NSIS_EXECUTABLE}" "${CMAKE_CURRENT_BINARY_DIR}/settings.nsi" "${CMAKE_CURRENT_SOURCE_DIR}/frepple.nsi"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    )  
  add_dependencies(installer frepple frepple-main doc)

else()
  message(WARNING "No windows installer can be created - missing NSIS")
endif()

endif()

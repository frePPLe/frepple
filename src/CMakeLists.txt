# Uncomment the next line to see the compiler commands
# set(CMAKE_VERBOSE_MAKEFILE ON)
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/frepple.rc.in"
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.rc"
)
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/frepple.ico"
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.ico"
  COPYONLY
)

# Auxilary static libraries
add_library(utils STATIC
  "utils/actions.cpp"
  "utils/date.cpp"
  "utils/library.cpp"
  "utils/python.cpp"
  "utils/xml.cpp"
  "utils/cache.cpp"
  "utils/database.cpp"
  "utils/json.cpp"
  "${CMAKE_SOURCE_DIR}/include/frepple/utils.h"
  "${CMAKE_SOURCE_DIR}/include/frepple/cache.h"
  "${CMAKE_SOURCE_DIR}/include/frepple/database.h"
  "${CMAKE_SOURCE_DIR}/include/frepple/xml.h"
  "${CMAKE_SOURCE_DIR}/include/frepple/json.h"
  "${CMAKE_BINARY_DIR}/include/config.h"
)
add_dependencies(utils venv)

add_library(model STATIC
  "model/actions.cpp"
  "model/buffer.cpp"
  "model/calendar.cpp"
  "model/customer.cpp"
  "model/demand.cpp"
  "model/flow.cpp"
  "model/flowplan.cpp"
  "model/item.cpp"
  "model/itemdistribution.cpp"
  "model/itemsupplier.cpp"
  "model/leveled.cpp"
  "model/library.cpp"
  "model/load.cpp"
  "model/loadplan.cpp"
  "model/location.cpp"
  "model/operation.cpp"
  "model/operationdependency.cpp"
  "model/operationplan.cpp"
  "model/pegging.cpp"
  "model/plan.cpp"
  "model/problem.cpp"
  "model/problems_buffer.cpp"
  "model/problems_operationplan.cpp"
  "model/problems_resource.cpp"
  "model/resource.cpp"
  "model/resourceskill.cpp"
  "model/setupmatrix.cpp"
  "model/skill.cpp"
  "model/solver.cpp"
  "model/suboperation.cpp"
  "model/supplier.cpp"
  "${CMAKE_SOURCE_DIR}/include/frepple/model.h"
)
add_dependencies(model utils)

add_library(solver STATIC
  "solver/operatordelete.cpp"
  "solver/solverbuffer.cpp"
  "solver/solverdemand.cpp"
  "solver/solverflow.cpp"
  "solver/solverload.cpp"
  "solver/solveroperation.cpp"
  "solver/solverplan.cpp"
  "solver/solverresource.cpp"
  "${CMAKE_SOURCE_DIR}/include/frepple/solver.h"
)
add_dependencies(solver model)

add_library(forecast STATIC
  "forecast/exprtk.h"
  "forecast/forecast.cpp"
  "forecast/forecast.h"
  "forecast/forecastsolver.cpp"
  "forecast/measure.cpp"
  "forecast/measure_compute.cpp"
  "forecast/timeseries.cpp"
)

if(MSVC)
  set_target_properties(forecast PROPERTIES
    COMPILE_FLAGS "/bigobj"
  )
endif()

add_dependencies(forecast solver)

# Main shared library
add_library(frepple SHARED
  dllmain.cpp
  tags.cpp
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.rc"
)
target_link_libraries(frepple PUBLIC utils)
target_link_libraries(frepple PUBLIC model)
target_link_libraries(frepple PUBLIC solver)
target_link_libraries(frepple PUBLIC xerces-c)
target_link_libraries(frepple PUBLIC forecast)

if(WIN32)
  target_link_libraries(frepple PRIVATE libpq)
  target_link_libraries(frepple PRIVATE ${Python3_LIBRARIES})
  set_target_properties(frepple PROPERTIES LINK_FLAGS "/ignore:4099")
  file(TO_NATIVE_PATH "${CMAKE_SOURCE_DIR}/bin/frepple.exe" frepple-exe)
  string(REPLACE "\\" "\\\\" frepple-exe-escaped "${frepple-exe}")
  add_custom_command(
    TARGET frepple
    PRE_LINK
    COMMAND WMIC PROCESS WHERE ExecutablePath='${frepple-exe-escaped}' DELETE
    COMMENT "Kill running frepple processes"
  )
else()
  target_link_libraries(frepple PRIVATE pq)
  target_link_libraries(frepple PRIVATE ${Python3_LIBRARIES})
endif()

install(
  TARGETS frepple
  DESTINATION "${CMAKE_INSTALL_LIBDIR}"
)

# Main executable
add_executable(frepple-main
  main.cpp
  "${CMAKE_SOURCE_DIR}/include/freppleinterface.h"
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.rc"
)
target_link_libraries(frepple-main LINK_PUBLIC frepple)
set_target_properties(frepple-main PROPERTIES
  OUTPUT_NAME "frepple"
  PDB_NAME_DEBUG "frepple-main"
)
install(
  TARGETS frepple-main
  DESTINATION "${CMAKE_INSTALL_BINDIR}"
)

# Put the compiled binaries in the source folder.
# This violates the out-of-source build principle, and mixes up multi-configuration builds.
# Only excuse is that it's convenient.
add_custom_command(
  TARGET frepple POST_BUILD VERBATIM
  COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:frepple>" "${CMAKE_SOURCE_DIR}/bin"
)
add_custom_command(
  TARGET frepple-main POST_BUILD VERBATIM
  COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:frepple-main>" "${CMAKE_SOURCE_DIR}/bin"
)

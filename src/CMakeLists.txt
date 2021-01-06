
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
  "${CMAKE_SOURCE_DIR}/include/frepple/utils.h"
  "${CMAKE_SOURCE_DIR}/include/frepple/xml.h"
  "${CMAKE_BINARY_DIR}/include/config.h"
  )

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
  "model/operationplan.cpp"
  "model/pegging.cpp"
  "model/plan.cpp"
  "model/problem.cpp"
  "model/problems_buffer.cpp"
  "model/problems_demand.cpp"
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

# Main shared library
add_library(frepple SHARED
  dllmain.cpp
  tags.cpp
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.rc"
  )
target_link_libraries(frepple LINK_PUBLIC utils)
target_link_libraries(frepple LINK_PUBLIC model)
target_link_libraries(frepple LINK_PUBLIC solver)
target_link_libraries(frepple LINK_PUBLIC xerces-c)
target_link_libraries(frepple LINK_PUBLIC ${PYTHON_LIBRARIES})
install(
  TARGETS frepple
  DESTINATION "${CMAKE_INSTALL_LIBDIR}"
  )

# Main executable
add_executable (frepple-main
  main.cpp
  "${CMAKE_SOURCE_DIR}/include/freppleinterface.h"
  "${CMAKE_CURRENT_BINARY_DIR}/frepple.rc"
  )
target_link_libraries (frepple-main LINK_PUBLIC frepple)
set_target_properties(frepple-main PROPERTIES OUTPUT_NAME "frepple")
install(
  TARGETS frepple-main
  DESTINATION "${CMAKE_INSTALL_BINDIR}"
  )

# Put the compiled binaries in the source folder.
# This violates the out-of-source build principle, and mixes up multi-configuration builds.
# Only excuse is that it's convenient.
set_target_properties(frepple-main PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/bin" )
set_target_properties(frepple-main PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}/bin" )
set_target_properties(frepple PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/bin" )
set_target_properties(frepple PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}/bin" )
set_target_properties(frepple PROPERTIES LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/bin" )
set_target_properties(frepple PROPERTIES LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}/bin" )

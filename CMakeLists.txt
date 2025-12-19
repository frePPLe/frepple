
set(CMAKE_VERBOSE_MAKEFILE ON)
cmake_minimum_required(VERSION 3.16)

# The version is defined in 2 places:
#  - pyproject.toml
#  - this file, next line
project(frepple VERSION 9.13.0)

set(PROJECT_EDITION "Community Edition")
set(PROJECT_BRANCH "community")

if(CMAKE_SYSTEM_NAME MATCHES "Linux")
  # Detect the linux distribution
  if(EXISTS "/etc/issue")
    file(READ "/etc/issue" LINUX_ISSUE)

    # Ubuntu 24
    if(LINUX_ISSUE MATCHES "Ubuntu 24")
      set(CPACK_GENERATOR "DEB")
      set(DISTRO "ubuntu24")

    # Ubuntu development
    elseif(LINUX_ISSUE MATCHES "Ubuntu.*development")
      set(CPACK_GENERATOR "DEB")
      set(DISTRO "ubuntudevel")
    endif()
  endif()

  if(NOT DISTRO)
    message(WARNING "FrePPLe has not been tested on this linux distribution.")
  endif()
endif()

# Check third party libraries
if(WIN32)
  # Some hard-coded paths for third party libraries on Windows.
  set(XERCESC_FOLDER "/develop/xerces-c-3.2.3")

  if(EXISTS "${XERCESC_FOLDER}")
    include_directories("${XERCESC_FOLDER}/include")
    list(APPEND CMAKE_REQUIRED_INCLUDES "${XERCESC_FOLDER}/include")
    add_library(xerces-c STATIC IMPORTED)
    set_target_properties(xerces-c PROPERTIES
      IMPORTED_LOCATION_DEBUG "${XERCESC_FOLDER}/lib/xerces-c_3D.lib"
      IMPORTED_LOCATION_RELEASE "${XERCESC_FOLDER}/lib/xerces-c_3.lib"
      IMPORTED_LOCATION_MINSIZEREL "${XERCESC_FOLDER}/lib/xerces-c_3.lib"
      IMPORTED_LOCATION_RELWITHDEBINFO "${XERCESC_FOLDER}/lib/xerces-c_3.lib"
    )
  endif()

  # PostgreSQL ZIP-installer from https://www.enterprisedb.com/download-postgresql-binaries
  # Used to embed PostgreSQL in frepple's windows installer
  set(POSTGRES_FOLDER "c:/develop/pgsql")
else()
  find_library(xerces-c NAMES xerces-c)

  if(NOT xerces-c)
    message(FATAL_ERROR "xerces-c library not found")
  endif()
endif()

if(UNIX)
  set(CMAKE_INSTALL_PREFIX "/")
  include(GNUInstallDirs)
else()
  set(CMAKE_INSTALL_LIBDIR "bin")
  set(CMAKE_INSTALL_SYSCONFDIR "custom")
  set(CMAKE_INSTALL_DATADIR "custom")
  set(CMAKE_INSTALL_BINDIR "custom")
  set(CMAKE_INSTALL_INCLUDEDIR "include")
endif()

# Check python and create the virtualenv
if(WIN32)
  set(Python3_VENV "${PROJECT_SOURCE_DIR}/venv/Scripts")
else()
  set(Python3_VENV "${PROJECT_SOURCE_DIR}/venv/bin")
endif()

find_package(Python3 3.8 COMPONENTS Interpreter Development REQUIRED)
add_custom_command(
  OUTPUT venv.stamp
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt" "${CMAKE_CURRENT_SOURCE_DIR}/requirements.dev.txt"
  COMMAND "${Python3_EXECUTABLE}" -m venv "${PROJECT_SOURCE_DIR}/venv" || cd .
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/requirements.dev.txt" requirements.dev.txt
  COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_CURRENT_SOURCE_DIR}/requirements.txt" requirements.txt
  COMMAND "${Python3_VENV}/pip" install -r requirements.dev.txt
  COMMAND ${CMAKE_COMMAND} -E touch venv.stamp
)
add_custom_target(venv DEPENDS venv.stamp)

find_program(npm NAMES npm)
find_program(grunt NAMES grunt)

if(grunt)
  add_custom_target(
    grunt
    COMMAND grunt
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  )
endif()

# C++ compiler flags and features
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(WIN32)
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MT")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MT /EHsc /MP8 ")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -D_DEBUG /MTd /EHsc /MP8 ")
  add_definitions("-D_CRT_SECURE_NO_DEPRECATE")
else()
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-error=date-time")
  set(CMAKE_CXX_FLAGS_PROFILING "${CMAKE_CXX_FLAGS_DEBUG} -DNDEBUG")
  set(CMAKE_C_FLAGS_PROFILING "${CMAKE_C_FLAGS_DEBUG} -DNDEBUG")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -Wuninitialized -Wunused -Wswitch")
  set(CMAKE_EXE_LINKER_FLAGS_PROFILING "")
  set(CMAKE_SHARED_LINKER_FLAGS_PROFILING "")
endif()

include(CheckIncludeFile)
include(CheckIncludeFileCXX)
include(CheckFunctionExists)
check_include_file(sys/prctl.h HAVE_SYS_PRCTL_H)
check_include_file(errno.h HAVE_ERRNO_H)
check_include_file(unistd.h HAVE_UNISTD_H)
check_include_file(crypt.h HAVE_CRYPT_H)
check_function_exists(truncate HAVE_TRUNCATE)
check_function_exists(localtime_r HAVE_LOCALTIME_R)
check_function_exists(dup2 HAVE_DUP2)
check_function_exists(memset HAVE_MEMSET)
check_function_exists(strncasecmp HAVE_STRNCASECMP)
check_function_exists(strnicmp HAVE_STRNICMP)
check_function_exists(strptime HAVE_STRPTIME)
check_function_exists(prctl HAVE_PRCTL)

# Verify third party header files
check_include_file_cxx("xercesc/util/XercesDefs.hpp" HAVE_XERCESC)

if(NOT ${HAVE_XERCESC})
  message(FATAL_ERROR "xerces-c include headers not found")
endif()

find_program(pg_config NAMES pg_config)

if(pg_config)
  execute_process(
    COMMAND ${pg_config} --libdir
    OUTPUT_VARIABLE POSTGRES_LIB
    ERROR_QUIET
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  execute_process(
    COMMAND ${pg_config} --includedir
    OUTPUT_VARIABLE POSTGRES_INCLUDE
    ERROR_QUIET
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  link_directories("${POSTGRES_LIB}")
  include_directories(${POSTGRES_INCLUDE})
  list(APPEND CMAKE_REQUIRED_INCLUDES "${POSTGRES_INCLUDE}")
  check_include_file("libpq-fe.h" HAVE_LIBPQ)

  if(NOT HAVE_LIBPQ)
    message("PostgreSQL include headers not found ${HAVE_LIBPQ}")
  endif()
else()
  message(FATAL_ERROR "PostgreSQL pg_config not found")
endif()

# C++ header file locations
include_directories(
  "${CMAKE_SOURCE_DIR}/include"
  "${CMAKE_BINARY_DIR}/include"
  "${Python3_INCLUDE_DIRS}"
)
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/include/config.h.in"
  "${CMAKE_CURRENT_BINARY_DIR}/include/config.h"
)

# File installation
install(
  FILES frepplectl.py
  DESTINATION "${CMAKE_INSTALL_BINDIR}"
  RENAME frepplectl
  PERMISSIONS OWNER_EXECUTE OWNER_READ GROUP_EXECUTE GROUP_READ
)
install(
  FILES djangosettings.py
  DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/frepple"
)
install(
  FILES requirements.txt
  DESTINATION "${CMAKE_INSTALL_DATADIR}/frepple"
)

# Packaging of the django app: Python module in a virtual environment
# Note that we use \$ to delay the evaluation till install time
execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import sys; print(sys.prefix)"
  OUTPUT_VARIABLE PYTHON_PREFIX
  ERROR_QUIET
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
install(CODE "execute_process(COMMAND mkdir -p \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple)")
install(CODE "execute_process(COMMAND ${Python3_EXECUTABLE} -m venv \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv)")
install(CODE "execute_process(COMMAND \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin/activate)")
install(CODE "execute_process(COMMAND \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin/pip3 install pip install --upgrade pip wheel six appdirs setuptools)")
install(CODE "execute_process(COMMAND \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin/python3 -m pip install --quiet ${PROJECT_SOURCE_DIR})")
install(CODE "execute_process(COMMAND \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin/pip3 install -r ${CMAKE_SOURCE_DIR}/requirements.txt)")
install(CODE "execute_process(COMMAND \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin/python3 -m pip install --quiet ${PROJECT_SOURCE_DIR})")
install(CODE "execute_process(COMMAND rm \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/lib64)")
install(CODE "execute_process(COMMAND find \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv -type f -exec sed -i \"s|/usr/bin/env python$  |/usr/bin/env python3|g\" {} \;)")
install(CODE "execute_process(COMMAND find \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin -type f -name \"*ctivate*\" -exec sed -i \"s|\$ENV{DESTDIR}||g\" {} \\;)")
install(CODE "execute_process(COMMAND find \$ENV{DESTDIR}/${CMAKE_INSTALL_DATADIR}/frepple/venv/bin -type f -executable -exec sed -i \"s|\$ENV{DESTDIR}||g\" {} \\;)")

# Packaging of the static files
install(CODE "execute_process(COMMAND ${CMAKE_COMMAND} -E env FREPPLE_STATIC=\$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_DATADIR}/frepple/static ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/frepplectl.py collectstatic --noinput --clear --ignore '*.less' --verbosity=0)")

# Generic packaging
set(CPACK_PACKAGE_VENDOR "frePPLe")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "FrePPLe is an open source production planning and scheduling application.")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})
set(CPACK_PACKAGE_FILE_NAME "${DISTRO}-${PROJECT_NAME}-${CPACK_PACKAGE_VERSION}")
set(CPACK_SOURCE_GENERATOR "TGZ")
set(CPACK_SOURCE_IGNORE_FILES
  "__pycache__"
  "^${PROJECT_SOURCE_DIR}/\\\\.git"
  "^${PROJECT_SOURCE_DIR}/\\\\.vs"
  "^${PROJECT_SOURCE_DIR}/\\\\.settings"
  "^${PROJECT_SOURCE_DIR}/logs/"
  "^${PROJECT_SOURCE_DIR}/build.*"
  "^${PROJECT_SOURCE_DIR}/venv/.*"
  "^${PROJECT_SOURCE_DIR}/static$"
  "^${PROJECT_SOURCE_DIR}/localsettings.*py$"
  "^${PROJECT_SOURCE_DIR}/node_modules"
  "^${PROJECT_SOURCE_DIR}/bin/.*\\\\.exe$"
  "^${PROJECT_SOURCE_DIR}/bin/frepple$"
  "^${PROJECT_SOURCE_DIR}/bin/frepple.dll$"
  "^${PROJECT_SOURCE_DIR}/bin/libfrepple.*"
  "^${PROJECT_SOURCE_DIR}/bin/.*\\\\.pdb$"
)

# Add folders
add_subdirectory(bin)
add_subdirectory(src)
add_subdirectory(doc)
add_subdirectory(contrib/docker)
add_subdirectory(contrib/linux)

# Debugging targets
find_program(valgrind NAMES valgrind)

if(valgrind)
  add_custom_target(
    callgrind
    DEPENDS venv
    COMMAND ${CMAKE_COMMAND} -E env
    FREPPLE_HOME=${CMAKE_SOURCE_DIR}/bin
    VIRTUAL_ENV=${CMAKE_SOURCE_DIR}/venv
    PYTHONPATH=${CMAKE_SOURCE_DIR}
    DJANGO_SETTINGS_MODULE=freppledb.settings
    FREPPLE_LOGFILE=frepple.log
    LD_BIND_NOW=1
    fcst=1
    invplan=1
    supply=1
    nowebservice=1
    constraint=13
    plantype=1
    valgrind --tool=callgrind
    ${CMAKE_SOURCE_DIR}/bin/frepple
    ${CMAKE_SOURCE_DIR}/freppledb/common/commands.py
    COMMAND callgrind_annotate --show-percs=yes > callgrind.relative.out
    COMMAND callgrind_annotate --show-percs=yes --inclusive=yes > callgrind.cumulative.out
    COMMAND callgrind_annotate --show-percs=yes --inclusive=yes --tree=calling > callgrind.cumulative_with_calling.out
    COMMAND callgrind_annotate --show-percs=yes --inclusive=yes --tree=caller > callgrind.cumulative_with_caller.out

    # Useful callgrind commands during a profiling run:
    # - callgrind_control: Return process id of the current callgrind rung
    # - callgrind_control -i off <pid>: Switch off the collection of metrics
    # - callgrind_control -i on <pid>: Switch on the collection of metrics
    # - callgrind_control -z <pid>: Clear out all metrics collected so far
  )
  add_custom_target(
    memcheck
    DEPENDS venv
    COMMAND ${CMAKE_COMMAND} -E
    env
    FREPPLE_HOME=${CMAKE_SOURCE_DIR}/bin
    PYTHONPATH=${CMAKE_SOURCE_DIR}
    DJANGO_SETTINGS_MODULE=freppledb.settings
    FREPPLE_LOGFILE=frepple.log
    LD_BIND_NOW=1
    invplan=1
    supply=1
    nowebservice=1
    constraint=13
    plantype=1
    PYTHONMALLOC=malloc
    valgrind --tool=memcheck -v
    ${CMAKE_SOURCE_DIR}/bin/frepple
    ${CMAKE_SOURCE_DIR}/freppledb/common/commands.py
  )
  add_custom_target(
    massif
    DEPENDS venv
    COMMAND ${CMAKE_COMMAND} -E
    env
    FREPPLE_HOME=${CMAKE_SOURCE_DIR}/bin
    PYTHONPATH=${CMAKE_SOURCE_DIR}
    DJANGO_SETTINGS_MODULE=freppledb.settings
    FREPPLE_LOGFILE=frepple.log
    LD_BIND_NOW=1
    invplan=1
    supply=1
    nowebservice=1
    constraint=13
    plantype=1
    PYTHONMALLOC=malloc
    valgrind --tool=massif
    ${CMAKE_SOURCE_DIR}/bin/frepple
    ${CMAKE_SOURCE_DIR}/freppledb/common/commands.py
    COMMAND ls -t massif.out.* | head -1 | xargs ms_print > memory_allocations.log
  )
endif()

find_program(gdb NAMES gdb)

if(gdb)
  add_custom_target(gdb ${CMAKE_COMMAND} -E
    env
    FREPPLE_HOME=${CMAKE_SOURCE_DIR}/bin
    PYTHONPATH=${CMAKE_SOURCE_DIR}
    DJANGO_SETTINGS_MODULE=freppledb.settings
    FREPPLE_LOGFILE=frepple.log
    supply=1
    constraint=13
    plantype=1
    gdb -ex=r --args ${CMAKE_SOURCE_DIR}/bin/frepple ${CMAKE_SOURCE_DIR}/freppledb/common/commands.py
  )
endif()

# Translations process:
# 1) Run "cmake --build . --target translations_extract" to get all translatable strings from the source code.
# 2) Translate all strings local/<LANGUAGE>/<LANGUAGE>.po file. The real work!
# 3) Run "make  --build . --target compile-translations" to merge the translations into the right places.
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
  add_custom_target(translations_extract
    COMMAND ${CMAKE_SOURCE_DIR}/translations.sh extract
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  )
  add_custom_target(translations_compile
    COMMAND ${CMAKE_SOURCE_DIR}/translations.sh compile
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  )
endif()

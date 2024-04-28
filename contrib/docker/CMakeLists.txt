
find_program(docker NAMES docker)

if(docker)
  # Main build & runtime image
  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/ubuntu-20.04.dockerfile" ubuntu-20.04/dockerfile COPYONLY)
  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/entrypoint.sh" ubuntu-20.04/entrypoint.sh COPYONLY)
  configure_file("${CMAKE_SOURCE_DIR}/requirements.txt" ubuntu-20.04/requirements.txt COPYONLY)
  add_custom_target(
    "docker-ubuntu-20.04"
    COMMAND ${CMAKE_COMMAND} --build . --target package_source
    COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/frepple-${PROJECT_VERSION}-Source.tar.gz" "${CMAKE_CURRENT_BINARY_DIR}/ubuntu-20.04/"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build --progress=plain --target package --output type=local,dest=. ubuntu-20.04
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build ubuntu-20.04
    --progress=plain
    --tag "frepple-${PROJECT_BRANCH}-ubuntu-20.04:${PROJECT_VERSION}"
    --label "org.opencontainers.image.title=frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.description=Docker image for frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.url=https://github.com/frePPLe/frepple/pkgs/container/frepple-${PROJECT_BRANCH}"
    --label "org.opencontainers.image.ref.name=frepple ${PROJECT_EDITION}"
    --label "org.opencontainers.image.version=${PROJECT_VERSION}"
  )

  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/ubuntu-24.04.dockerfile" ubuntu-24.04/dockerfile COPYONLY)
  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/entrypoint.sh" ubuntu-24.04/entrypoint.sh COPYONLY)
  configure_file("${CMAKE_SOURCE_DIR}/requirements.txt" ubuntu-24.04/requirements.txt COPYONLY)
  add_custom_target(
    "docker-ubuntu-24.04"
    COMMAND ${CMAKE_COMMAND} --build . --target package_source
    COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/frepple-${PROJECT_VERSION}-Source.tar.gz" "${CMAKE_CURRENT_BINARY_DIR}/ubuntu-devel/"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build --progress=plain --target package --output type=local,dest=. ubuntu-devel
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build ubuntu-devel
    --progress=plain
    --tag "frepple-${PROJECT_BRANCH}-ubuntu-24.04:${PROJECT_VERSION}"
    --tag "frepple-${PROJECT_BRANCH}:${PROJECT_VERSION}"
    --tag "ghcr.io/frepple/frepple-${PROJECT_BRANCH}:${PROJECT_VERSION}"
    --label "org.opencontainers.image.title=frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.description=Docker image for frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.url=https://github.com/frePPLe/frepple/pkgs/container/frepple-${PROJECT_BRANCH}"
    --label "org.opencontainers.image.ref.name=frepple ${PROJECT_EDITION}"
    --label "org.opencontainers.image.version=${PROJECT_VERSION}"
  )
  add_custom_target(
    "docker"
    DEPENDS docker-ubuntu-24.04
  )

  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/ubuntu-devel.dockerfile" ubuntu-devel/dockerfile COPYONLY)
  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/entrypoint.sh" ubuntu-devel/entrypoint.sh COPYONLY)
  configure_file("${CMAKE_SOURCE_DIR}/requirements.txt" ubuntu-devel/requirements.txt COPYONLY)
  add_custom_target(
    "docker-ubuntu-devel"
    COMMAND ${CMAKE_COMMAND} --build . --target package_source
    COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/frepple-${PROJECT_VERSION}-Source.tar.gz" "${CMAKE_CURRENT_BINARY_DIR}/ubuntu-devel/"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build --progress=plain --target package --output type=local,dest=. ubuntu-devel
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build ubuntu-devel
    --progress=plain
    --tag "frepple-${PROJECT_BRANCH}-ubuntu-devel:${PROJECT_VERSION}"
  )

  configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/docker-compose.yml.in"
    "${CMAKE_CURRENT_BINARY_DIR}/docker-compose.yml"
  )
  add_custom_target(
    "docker-up"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} compose
    --project-name frepple-${PROJECT_BRANCH}
    up
    --detach
  )
  add_custom_target(
    "docker-down"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} compose
    --project-name frepple-${PROJECT_BRANCH}
    down
  )
endif()

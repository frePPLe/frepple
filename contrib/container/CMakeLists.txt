
find_program(docker NAMES docker)

if(docker)
  execute_process(
    COMMAND git log -1 --pretty=%ct
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    OUTPUT_VARIABLE SOURCE_DATE_EPOCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  configure_file("${CMAKE_CURRENT_SOURCE_DIR}/dockerfile" build-context/dockerfile COPYONLY)
  add_custom_target(
    "docker"
    COMMAND ${CMAKE_COMMAND} -E env SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH} ${CMAKE_COMMAND} --build . --target package_source  
    COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/frepple-${PROJECT_VERSION}-Source.tar.gz" "${CMAKE_CURRENT_BINARY_DIR}/build-context/"
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build build-context
    --progress=plain
    --tag "frepple-${PROJECT_BRANCH}:${PROJECT_VERSION}"
    --tag "ghcr.io/frepple/frepple-${PROJECT_BRANCH}:${PROJECT_VERSION}"
    --label "org.opencontainers.image.title=frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.description=Docker image for frepple ${PROJECT_EDITION} ${PROJECT_VERSION}"
    --label "org.opencontainers.image.url=https://github.com/frePPLe/frepple/pkgs/container/frepple-${PROJECT_BRANCH}"
    --label "org.opencontainers.image.ref.name=frepple ${PROJECT_EDITION}"
    --label "org.opencontainers.image.version=${PROJECT_VERSION}"
  )
endif()


find_program(docker NAMES docker)
find_program(gpg NAMES gpg)

if (docker)

foreach(dist ubuntu-18.04 ubuntu-20.04 opensuse-15.1 centos-8 debian-10 alpine-3)
  configure_file(${CMAKE_CURRENT_SOURCE_DIR}/${dist}.dockerfile ${dist}/dockerfile COPYONLY)
  add_custom_target(
    "docker-${dist}"
    #COMMAND "${CMAKE_COMMAND}" --build . --target package_source
    COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
      ${docker} build --target package --output type=local,dest=. ${dist}
    )
endforeach()

set(RHEL_USER  "Red Hat user name")
set(RHEL_PASSWORD "Red Hat password")
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/rhel-8.dockerfile rhel-8/dockerfile COPYONLY)
#if(gpg)
#$(GPG) --export-secret-keys -a devops@frepple.com >gpg_key
#endif()
add_custom_target(
  "docker-rhel-8"
  #COMMAND "${CMAKE_COMMAND}" --build . --target package_source
  COMMAND ${CMAKE_COMMAND} -E env DOCKER_BUILDKIT=1
    ${docker} build 
      --target package 
      --output type=local,dest=.
      --build-arg RHEL_USER=${RHEL_USER}
      --build-arg RHEL_PASSWORD=${RHEL_PASSWORD} 
      rhel-8
  )

endif()

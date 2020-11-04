
This directory contains docker containers to build packages for various Linux distributions.
What a cacophony of many well-intended-but-tiresome packaging variations!

It builds 2-stage docker images.
- The first stage builds the binary .RPM or .DEB packages.
- The second stage is a runtime image to deploy frePPLe inside a docker container.

CAUTION: The runtime images are NOT considered ready for production deployments!
The following areas need to be resolved for this:
- The process management in the runtime image is not up to the docker standard. This can result in problems to stop the container cleanly.
- The task scheduler feature in frepple relies on the atd daemon, which is not available in the runtime container images. 

A quick reference of some handy extra commands:

 - Interactive shell:
   docker run -i -t --rm=true -v `pwd`:/mnt/myfiles <image> /bin/bash

 - Copy data from the builder image
   id=$(docker create opensuse-builder-6.1.0)
   docker cp $id:/home/builder/rpm/RPMS - > rpms.tar
   docker rm -v $id
   tar xvf rpms.tar

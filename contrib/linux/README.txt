
This directory contains builds for various linux distributions.

It builds 2-stage docker images.
- The first stage builds the binary .RPM or .DEB packages.
- The second stage is a runtime image to deploy frePPLe inside a docker container.


A quick reference of some handy commands:

 - Interactive shell:
   docker run -i -t --rm=true <image> /bin/bash

 - Copy data from the builder image
   id=$(docker create opensuse-builder-6.1.0)
   docker cp $id:/home/builder/rpm/RPMS - > rpms.tar
   docker rm -v $id
   tar xvf rpms.tar


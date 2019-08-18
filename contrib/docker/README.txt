
This directory contains a docker (see https://www.docker.com/) configuration
file to build and deploy frePPLe in an Ubuntu container.

This setup is in beta stage, with some rough edges:
- Postgres data on its own volume
- Configure djangosettings correctly
- Doesn't run under LCOW due to a bug with the copy command. 
  See https://blog.docker.com/2017/11/docker-for-windows-17-11/
  and https://github.com/moby/moby/issues/33850 for the bug.

Helping hands and contributions are welcome!

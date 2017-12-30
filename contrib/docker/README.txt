
This directory contains a docker (see https://www.docker.com/) configuration
file to build and run frePPLe in an Ubuntu container.

This setup is not production-ready yet, missing the following
key pieces:
- PostgreSQL database must be passed to the container
- Djangosettings.py must be updated to use the right database connection
- Apache web server must correctly run in the foreground
- Doesn't run under LCOW due to a bug with the copy command. 
  See https://blog.docker.com/2017/11/docker-for-windows-17-11/
  and https://github.com/moby/moby/issues/33850 for the bug.
- Log file management

Helping hands and contributions are welcome!

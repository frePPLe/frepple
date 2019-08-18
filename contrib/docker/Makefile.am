#
# Process this file with automake to produce Makefile.in
#

EXTRA_DIST = dockerfile README.txt docker-compose.yml

contrib:
	docker build -t frepple .
	docker-compose build
  
runtime:
	docker-compose up

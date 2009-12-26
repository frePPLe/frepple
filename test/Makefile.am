#
# Process this file with automake to produce Makefile.in
#

SUBDIRS = cluster scalability_1 scalability_2 scalability_3 datetime flow_alternate_1 flow_alternate_2 constraints_combined_1 constraints_leadtime_1 lpsolver_1 constraints_material_1 constraints_material_2 constraints_material_3 jobshop xml forecast_1 forecast_2 forecast_3 forecast_4 forecast_5 constraints_resource_1 constraints_resource_2 constraints_resource_3 constraints_resource_4 constraints_resource_5 problems deletion operation_alternate operation_available operation_effective operation_pre_post operation_routing name multithreading sample_module callback pegging xml_remote python_1 python_2 python_3 demand_policy safety_stock buffer_procure_1 flow_effective load_alternate load_effective setup_1 setup_2

EXTRA_DIST = runtest.py

if LP 
check:
	./runtest.py ${TESTARGS}
else
check:
	./runtest.py ${TESTARGS} -e lpsolver_1
endif

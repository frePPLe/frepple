from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^problems/', 'frepple.output.views.problems'),

    # Uncomment this for admin:
    (r'^admin/', include('django.contrib.admin.urls')),
)

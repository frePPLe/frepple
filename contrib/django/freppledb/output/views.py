from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
#from django.contrib.auth import authenticate
#from django.contrib.auth.decorators import login_required
from frepple.output.models import Problem
from django.contrib.admin.views.main import change_list

def problems(request):
    #problem_list = Problem.objects.all().order_by('start')
    #return render_to_response('output/problems.html', {'problem_list': problem_list})
    return change_list(request, 'output', 'problem')



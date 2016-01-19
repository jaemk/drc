from django.shortcuts import render

from django.http import HttpResponse as httpresp
from django.http import HttpResponseRedirect as httprespred

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .models import Block
from .models import DrawingStatus
from .models import Department
from .models import Drawing
from .models import Revision
from .models import Comment
from .models import Reply

from .forms import SearchForm

def _get_username(request):
    if request.user.is_authenticated():
        username = request.user
    else:
        username = None

    return username


def logout_view(request):
    username = request.user
    logout(request)
    return httpresp('''Goodbye {} !<br>
                    You\'ve successfully logged out!<br>
                    <a href="/">return to homepage</a>'''.format(username))


@login_required(login_url='/accounts/login')
def index(request):
    username = _get_username(request)
    return render(request, 'tracking/index.html', {'username':username})
    # return httpresp('Welcome to DRC tracking index')


@login_required(login_url='/accounts/login')
def search(request):
    username = _get_username(request)
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            pass
            # full_name = _add_student(username, form.cleaned_data)
            # student = Student.objects.get(full_name=full_name)

        # return httprespred('/tracking/search/results{}'.format())
        return httprespred('/tracking/')
    else:
        form = SearchForm()

    context = {'username':username, 'form':form.as_table()}
    return render(request, 'tracking/search.html', context)


# def detail_pdf(request, question_id):
#     try:
#         #question = Question.objects.all().exclude(pdf__endswith='file.pdf')
#         question = Question.objects.get(pk=question_id)
#         if question.pdf != '':
#             filepath = question.pdf
#         else:
#             raise http404('No drawing for question: {}'.format(question.question_text))
#     except Question.DoesNotExist:
#         raise http404('Question does not exist')

#     with open(str(filepath), 'rb') as pdffile:
#         response = httpresp(pdffile.read(), content_type='application/pdf')
#         response['Content-Disposition'] = 'filename=file.pdf'
#         return response
#     #return httpresp(file.read()

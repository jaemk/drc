from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from tracking.models import Block
from tracking.models import Drawing
from tracking.models import Revision
from tracking.models import Comment

from tracking.forms import SearchForm

#---------------------- Drawing Search ------------------------
def _pull_drawings(formdat):
    ''' Replace wildcards '*' with regex '.*'
        filter drawing names with optional qualifiers 
        return a drawing query set '''
    
    if not formdat['drawing_name']:
        return None
    # Apply drawing search qualifiers:
    #   start with simplest first, saving regex
    #   search for last - return as soon as null

    cquery = None
    # Fetch all comments that match selected comment status
    if formdat['comment_status']:
        com_stat = formdat['comment_status'] # list of selections
        if len(com_stat) > 1:   # user selected both options
            cquery = Comment.objects.prefetch_related('revision').all()
        else:                   # user selected one option
            check = {'open':True, 'closed':False}
            cquery = Comment.objects.prefetch_related('revision')\
                                    .filter(status=check[com_stat[0]])
        if not cquery.exists():
            # there are no comments (so no drawings)
            # that match the selected status
            return

    # Create a Drawing query set
    if cquery:
        # If there is a comment set, use it to filter drawings
        revs = Revision.objects.prefetch_related('drawing')\
                        .filter(pk__in=cquery.values_list('revision', flat=True))
        dquery = Drawing.objects.filter(pk__in=revs.values_list('drawing', flat=True))
    else:
        dquery = Drawing.objects

    # Filter drawings by project
    if formdat['project']:
        dquery = dquery.filter(project=formdat['project'])

    # Filter drawings by discipline
    if formdat['discipline']:
        dquery = dquery.filter(discipline__in=formdat['discipline'])

    # Filter drawings based on Department name
    if formdat['department_name']:
        exp = formdat['department_name'].strip().lower().replace('*','.*')
        dquery = dquery.filter(department__name__regex=exp)

    # Filter drawings based on Block name
    if formdat['block_name']:
        exp = formdat['block_name'].strip().lower().replace('*','.*')
        blockquery = Block.objects.filter(name__regex=exp)
        dquery = dquery.filter(block__in=blockquery)

    # Filter drawings based on drawing status
    if formdat['drawing_status']:
        dquery = dquery.filter(status__in=formdat['drawing_status'])

    # Filter drawing set based on drawing name regex
    qstr = '^{}$'.format(formdat['drawing_name'].lower().replace('*','.*'))
    dquery = dquery.filter(name__regex=qstr).order_by('name')
    return dquery


@login_required
def drawing_search(request):
    ''' Serve up drawing search form with optional qualifiers '''
    user = request.user
    drawings = False
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            drawings = _pull_drawings(form.cleaned_data)

    else:
        form = SearchForm()

    context = {'username':user, 'form':form.as_table(), 
               'drawings':drawings}
    if drawings != False:
        return render(request, 'tracking/drawing_results.html', context)
    return render(request, 'tracking/drawing_search.html', context)



#---------------------- Revision Search ------------------------
@login_required
def revision_search(request):
    # add rev search form
    pass
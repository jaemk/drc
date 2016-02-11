import os
import sys
import mimetypes
import subprocess
from zipfile import ZipFile

from django.shortcuts import render
from django.http import HttpResponse as httpresp
from django.http import HttpResponseRedirect as httprespred
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from django.conf import settings

from tracking.models import Block
from tracking.models import DrawingStatus
from tracking.models import Department
from tracking.models import Drawing
from tracking.models import DrawingAttachment
from tracking.models import Revision
from tracking.models import RevisionAttachment
from tracking.models import Comment
from tracking.models import CommentAttachment
from tracking.models import Reply
from tracking.models import ReplyAttachment
from tracking.models import DrawingSubscription
ALL_MODELS = [Block, DrawingStatus, Department, Drawing, 
              DrawingAttachment, Revision, RevisionAttachment,
              Comment, CommentAttachment, Reply, ReplyAttachment,
              DrawingSubscription]


#----------------------  Backups Process, Serve ------------------------
@login_required
def backup(request):
    ''' backup menu '''
    if not request.user.is_superuser:
        return httprespred(reverse('tracking:index'))
    user = request.user
    return render(request, 'tracking/dump_menu.html', {'username':user})


def _extract_to_csv(zip_name, zip_path):
    folder = os.path.dirname(zip_path)
    os.chdir(folder)
    files = []
    for table in ALL_MODELS:
        name = table.__name__
        files.append(name+'.csv')
        info = table.objects.all()
        keys = [k for k in info[0].__dict__.keys() if not k.startswith('_')]
        with open('{}.csv'.format(name), 'w') as fout:
            fout.write(','.join(keys)+'\n')
            for line in info:
                items = []
                for key in keys:
                    # have to reformat the date -_-
                    if 'date' not in key:
                        items.append(str(line.__dict__[key]).replace('\n','_')\
                                        .replace('\t','_'))
                    else:
                        try:
                            items.append(line.__dict__[key].strftime('%m-%d-%Y'))
                        except:
                            items.append(str(line.__dict__[key]).replace('\n','_')\
                                        .replace('\t','_'))

                fout.write(','.join(items)+'\n')
                # fout.write(','.join([str(line.__dict__[key]).replace('\n','_')\
                #                         .replace('\t','_')
                #                         for key in keys])+'\n')

    os.chdir(settings.BASE_DIR)
    return files
                

@login_required
def dump_data(request, dump_type):
    ''' Dump database json to
        /backup/user/ or /backup/auto '''
    if not request.user.is_superuser:
        return httprespred(reverse('tracking:index'))

    if dump_type == 'json':
        zip_name = 'data_user_json_dump.zip'
        dump_name = 'data_user_dump.json'
        dump_names = [dump_name]
        dump_path = os.path.join(settings.BASE_DIR, 'backup', 'user', dump_name)
        zip_path = os.path.join(settings.BASE_DIR, 'backup', 'user', zip_name)

        subprocess.call([sys.executable, 'manage.py', 
                        'dumpdata', '--indent', '2',
                        '--verbosity', '0',
                        '-o', dump_path], env=os.environ.copy())

    else: #dump_type=='csv':
        zip_name = 'data_user_csv_dump.zip'
        zip_path = os.path.join(settings.BASE_DIR, 'backup', 'user', zip_name)
        dump_names = _extract_to_csv(zip_name, zip_path)

    os.chdir(os.path.dirname(zip_path))
    with ZipFile(zip_name, 'w') as zip_dump:
        for item in dump_names:
            zip_dump.write(item)
    os.chdir(settings.BASE_DIR)

    try:
        with open(zip_path, 'rb') as dump:
            response = httpresp(dump.read(), content_type=mimetypes.guess_type(zip_path)[0])
            response['Content-Disposition'] = 'filename={}'.format(zip_name)
            response['Set-Cookie'] = 'fileDownload=true; path=/'
            return response
    except Exception as ex:
        return httpresp('''Error: {} <br/>
                        Unable to serve file: {}
                        </br>Please notify James Kominick
                        </br>Close this tab'''\
                        .format(ex, zip_name))

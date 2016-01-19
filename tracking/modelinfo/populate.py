from ..models import Block
from ..models import DrawingStatus
from ..models import Department
from ..models import Discipline
from ..models import DrawingKind
from ..models import Drawing
from ..models import Revision
from ..models import Comment
from ..models import Reply

import os

location = os.path.dirname(os.path.realpath(__file__))
block_file = 'blocks.csv'
department_file = 'departments.csv'
discipline_file = 'disciplines.csv'
drawing_file = 'drawings.csv'
drawing_kinds_file = 'drawing_kinds.csv'
drawing_status_file = 'drawing_statuses.csv'
expected_dates_file = 'expected_drawing_dates.csv'

def available():
    print('\n{}:'.format(location))
    for f in os.listdir(location):
        if os.path.isfile(os.path.join(location, f)):
            print('  -> {}'.format(f))

def _pack_info(keys, info_raw):
    info = {}
    for line in info_raw:
        items = line.split(',')
        for i, key in enumerate(keys):
            try:
                info[key].append(items[i].strip().lower())
            except KeyError:
                info[key] = []
    return info

def _parse_file(name=None, headers=True):
    if not name:
        return None
    file_path = os.path.join(location, name)
    with open(file_path, 'r') as f:
        info_raw = [line.strip('\n').strip() for line in f if line.strip('\n').strip() != '']

    if headers:
        head_raw = info_raw.pop(0)
        head = [item.strip().lower() for item in head_raw.split(',')]
        return _pack_info(head, info_raw)
    else:
        fhead = name.split('.')[0]
        info = {fhead:[]}
        for line in info_raw:
            info[fhead].append(line.strip().lower())
        return info


def add_blocks():
    print('Populating Blocks...')
    info = _parse_file(name=block_file, headers=False)
    keyval = block_file.split('.')[0]
    already = Block.objects.all()
    prev = [block.name for block in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_block = Block(name=item)
            new_block.save()
            added.append(item)
            print('  -> Added Block: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))


def add_drawing_statuses():
    info = _parse_file(name=drawing_status_file, headers=False)
    keyval = drawing_status_file.split('.')[0]
    already = DrawingStatus.objects.all()
    prev = [dwg_st.status for dwg_st in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_dwg_status = DrawingStatus(status=item)
            new_dwg_status.save()
            added.append(item)
            print('  -> Added Dwg Status: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))
    

def add_departments():
    info = _parse_file(name=department_file, headers=False)
    print(info)
    # new_dep = Department(name='')


def add_disciplines():
    info = _parse_file(name=discipline_file, headers=False)
    print(info)
    # new_disc = Discipline(name='')


def add_drawing_kinds():
    info = _parse_file(name=drawing_kinds_file, headers=False)
    print(info)
    # new_dwg_kind = DrawingKind(name='')


def add_drawings():
    info = _parse_file(name=drawing_file, headers=True)
    print(' | '.join(['{}:{}'.format(key, val[0]) for key, val in info.items()]))
    # new_dwg = Drawing(name='',
    #                   desc='')

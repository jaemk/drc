from ..models import Block
from ..models import Phase
from ..models import DrawingStatus
from ..models import Department
from ..models import Discipline
from ..models import DrawingKind
from ..models import Drawing
from ..models import Revision
from ..models import Comment
from ..models import Reply

import os
import datetime
from django.utils import timezone
import pytz

location = os.path.dirname(os.path.realpath(__file__))
block_file = 'blocks.csv'
phase_file = 'phases.csv'
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
        info_raw = [line.strip('\n').strip() for line in f\
                        if line.strip('\n').strip() != '']

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
    keyval = department_file.split('.')[0]
    already = Department.objects.all()
    prev = [dep.name for dep in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_dep = Department(name=item)
            new_dep.save()
            added.append(item)
            print('  -> Added Department: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))


def add_disciplines():
    info = _parse_file(name=discipline_file, headers=False)
    keyval = discipline_file.split('.')[0]
    already = Discipline.objects.all()
    prev = [disc.name for disc in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_disc = Discipline(name=item)
            new_disc.save()
            added.append(item)
            print('  -> Added Discipline: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))


def add_drawing_kinds():
    info = _parse_file(name=drawing_kinds_file, headers=False)
    keyval = drawing_kinds_file.split('.')[0]
    already = DrawingKind.objects.all()
    prev = [dwg_kind.name for dwg_kind in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_dwg_kind = DrawingKind(name=item)
            new_dwg_kind.save()
            added.append(item)
            print('  -> Added Dwg Kind: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))

def find_phases():
    print('finding phases in drawings.csv')
    info = _parse_file(name=drawing_file, headers=True)
    phases = set()
    for i in range(len(info[list(info.keys())[0]])):
            ph = info['phase'][i].lower()
            phases.add(ph)

    with open(os.path.join(location, 'phases.csv'), 'w') as pfile:
        for item in phases:
            print(item)
            pfile.write('{}\n'.format(item))



def add_phases():
    print('Looking for phase file')
    if phase_file not in os.listdir(location):
        print('phase file not found...')
        find_phases()

    print('Populating Phases...')
    info = _parse_file(name=phase_file, headers=False)
    keyval = phase_file.split('.')[0]
    already = Phase.objects.all()
    prev = [phase.number for phase in already]
    added = prev[:]
    print('->> Total already in: {}'.format(len(added)))
    for item in info[keyval]:
        if item not in added:
            new_phase = Phase(number=item)
            new_phase.save()
            added.append(item)
            print('  -> Added Phase: {}'.format(item))
    print('->> Total added: {}'.format(len(added) - len(prev)))


def add_drawings():
    info = _parse_file(name=drawing_file, headers=True)
    print(' | '.join(['{}:{}'.format(key, val[0]) for key, val in info.items()]))

    total = len(info[[i for i in info.keys()][0]])
    
    added = 0
    for i in range(total):
        name = info['name'][i].lower()
        if not Drawing.objects.filter(name=name).exists():
            print('-> {}'.format(info['block'][i]), end='')
            if info['block'][i] == '0':
                info['block'][i] = 'misc'
            block = Block.objects.get(name=info['block'][i]) if info['block'][i] \
                                                             and info['block'][i] != '0'\
                                                             and info['block'][i] != 'none'\
                                                             else None
            status = DrawingStatus.objects.get(status='new')
            dep = Department.objects.get(name=info['department'][i]) if info['department'][i] else None
            disc = Discipline.objects.get(name=info['discipline'][i]) if info['discipline'][i] else None
            kind = DrawingKind.objects.get(name=info['kind'][i]) if info['kind'][i] else None
            phase = Phase.objects.get(number=info['phase'][i]) if info['phase'][i] else None
            new_dwg = Drawing(name=name,
                              desc=info['desc'][i] if info['desc'][i] else None,
                              phase=phase,
                              #block=block,
                              status=status,
                              department=dep,
                              discipline=disc,
                              kind=kind,
                              )
            new_dwg.save()
            new_dwg.block.add(block)
            new_dwg.save()
            added += 1
            print('  -> Added Drawing: {}'.format(name))

    print('->> Total Added: {}'.format(added))


def add_expected_dates():
    info = _parse_file(name=expected_dates_file, headers=True)
    current_tz = pytz.timezone("America/New_York")
    for i in range(len(info['name'])):
        name = info['name'][i]
        if name:
            date = None
            exp_date = None
            if info['date'][i]:
                date = info['date'][i]
                exp_date = current_tz.localize(datetime.datetime.strptime(date, '%m/%d/%Y'), is_dst=None)
                

            if Drawing.objects.filter(name=name).exists(): 
                d = Drawing.objects.get(name=name)
                d.expected = exp_date
                d.save()
                #update(expected=exp_date)
            print(' -> updated {} with date {}'.format(name, exp_date))
        



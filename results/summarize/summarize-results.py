#!/usr/bin/env python3

import pandas

from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path
from tabulate import tabulate


########################################################################
#
#  common helper routines
#


COLUMN_REPLACEMENTS = (
    ('Alexi', 'UTL'),
    ('Jpype', 's-VPA'),
    ('SVPA', 's-VPA'),
    ('Over', '/'),
)


def rename_solvers(column):
    for replacement in COLUMN_REPLACEMENTS:
        column = column.replace(*replacement)
    return column


CSV_DIR = Path(__file__).parent


def read_csv(basename):
    path = (CSV_DIR / basename).with_suffix('.csv')
    frame = pandas.read_csv(path, index_col='App')
    frame.index = frame.index.str.replace('\\\_', '_')
    frame.index.rename('Application', inplace=True)
    frame.sort_values('Mean LoC', inplace=True)
    frame.rename(columns=rename_solvers, inplace=True)
    return frame


def caption_suffix(prefix):
    midfix = ' using stacks '
    suffix = {'csi': 'and call coverage', 'stack': 'only'}[prefix]
    return midfix + suffix


def show_table(kind, number, caption, frame, format):
    formatted = tabulate(frame, headers='keys', floatfmt=format, numalign='right', tablefmt='fancy_grid')
    print('\n{} {}. {}\n\n{}\n\n'.format(kind, number, caption, formatted))


########################################################################
#
#  display logic for specific types of data
#


def show_table_incompletes(number, prefix):
    frame = read_csv(prefix + '-incomplete')
    del frame['Mean LoC']
    frame.rename(columns={'Attempted': 'Variants'}, inplace=True)
    resources = ('Time', 'Memory')
    solvers = ('s-VPA', 'FSA', 'UTL')
    for solver in solvers:
        components = ['{} {}out'.format(solver, resource) for resource in resources]
        frame[solver] = frame[components].apply(tuple, axis=1)
        frame.drop(components, axis=1, inplace=True)
    midfix = caption_suffix(prefix)
    caption = 'Incomplete analyses{}: ({})'.format(midfix, ', '.join(resources))
    show_table('Table', number, caption, frame, 'd')


def show_table_relative_time(number, prefix):
    frame = read_csv(prefix + '-relative-time')
    del frame['Mean LoC']
    caption = 'UTL-relative analysis time' + caption_suffix(prefix)
    show_table('Figure', number, caption, frame, ',.1f')


def show_table_certain(number, prefix, precision):
    frame = read_csv(prefix + '-certain')
    frame = frame[['s-VPA', 'UTL']]
    caption = 'Basic blocks definitively categorized as “Yes” or “No”' + caption_suffix(prefix)
    formatter = '.{}%'.format(precision)
    show_table('Figure', number, caption, frame, formatter)


def show_table_2():
    frame = read_csv('applications')
    frame['Mean LoC'] = frame['Mean LoC'].astype(float)
    show_table('Table', 2, 'Evaluated applications', frame, ',.0f')


########################################################################
#
#  main dispatcher
#


def main():

    handlers = OrderedDict((
        ('table-2',   show_table_2),
        ('table-3',   lambda: show_table_incompletes(   3, 'stack')),
        ('figure-11', lambda: show_table_relative_time(11, 'stack')),
        ('figure-12', lambda: show_table_certain(      12, 'stack', 1)),
        ('table-4',   lambda: show_table_incompletes(   4, 'csi')),
        ('figure-13', lambda: show_table_relative_time(13, 'csi')),
        ('figure-14', lambda: show_table_certain(      14, 'csi', 0)),
    ))

    parser = ArgumentParser(description='Summarize experimental results.')
    parser.add_argument('--only', action='append', choices=handlers.keys(), help='table or figure to summarize; can be used multiple times; default shows everything, in paper order')
    only = parser.parse_args().only or handlers.keys()

    for key in only:
        handlers[key]()


if __name__ == '__main__':
    main()

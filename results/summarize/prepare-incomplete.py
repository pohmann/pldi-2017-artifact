#!/usr/bin/env python3

from sys import argv, stderr, stdout

import pandas


def main():
    csv = pandas.read_csv(argv[2], usecols=('Solver', 'App', 'Timeout', 'Memoryout'))
    csv['Attempted'] = 1
    pivot = csv.pivot_table(index='App', columns='Solver', aggfunc=sum)

    # validate attempt counts, save for later, and temporarily remove
    assert (pivot.Attempted.UTL == pivot.Attempted.FSA).all()
    # assert (pivot.Attempted.UTL == pivot.Attempted.SVPA).all()
    attempted = pivot.Attempted.UTL
    del pivot['Attempted']

    # identify and remove rows with neither timeouts nor memoryouts
    filter = (pivot.Timeout == 0) & (pivot.Memoryout == 0)
    filter = filter.SVPA & filter.FSA & filter.UTL
    pivot = pivot[~filter]

    # shuffle columns around to group by solver first, then by problem count
    pivot = pivot.reorder_levels([1, 0], axis=1)
    colindex = pandas.MultiIndex.from_product((
        ('SVPA', 'FSA', 'UTL'),
        ('Timeout', 'Memoryout'),
    ), names=('Solver', 'Count'))
    pivot = pivot.reindex_axis(colindex, 1)

    # flatten columns
    pivot.columns = [' '.join(pair) for pair in colindex.tolist()]

    # restore "Attempted" column
    pivot.insert(0, 'Attempted', attempted)

    # add LoC column for later sorting
    sizes = pandas.read_csv(argv[1], index_col='App', usecols=('App', 'Mean LoC'))
    pivot = pivot.join(sizes)

    # protect underscores from LaTeX and save for use by paper
    pivot.set_index(pivot.index.str.replace('_', '\\_'), inplace=True)
    pivot.to_csv(stdout, float_format='%.f')


if __name__ == '__main__':
    main()

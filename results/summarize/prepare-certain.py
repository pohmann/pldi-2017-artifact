#!/usr/bin/env python3

from sys import argv, stderr, stdout

import pandas


def main():
    # only consider analyses that completed
    csv = pandas.read_csv(argv[2], usecols=('Solver', 'App', 'Completed', 'Yes', 'No', 'Maybe'))
    csv = csv[csv.Completed]
    del csv['Completed']

    # compute fraction of answers that were certain: yes or no, not maybe
    certain = csv.Yes + csv.No
    csv['Certain'] = certain / (certain + csv.Maybe)
    for junk in 'Yes', 'No', 'Maybe':
        del csv[junk]

    # aggregate
    pivot = csv.pivot_table(index='App', columns='Solver')
    pivot.columns = pivot.columns.droplevel()

    # add LoC column for later sorting
    sizes = pandas.read_csv(argv[1], index_col='App', usecols=('App', 'Mean LoC'))
    pivot = pivot.join(sizes)

    # protect underscores from LaTeX and save for use by paper
    pivot.set_index(pivot.index.str.replace('_', '\\_'), inplace=True)
    pivot.to_csv(stdout)


if __name__ == '__main__':
    main()

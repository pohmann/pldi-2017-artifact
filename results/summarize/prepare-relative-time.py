#!/usr/bin/env python3

from sys import argv, stderr, stdout

import pandas


def main():
    # only consider analyses that completed
    csv = pandas.read_csv(argv[2], usecols=('Solver', 'App', 'Version', 'Fault', 'Completed', 'AnalysisTime'))
    csv = csv[csv.Completed]
    del csv['Completed']

    # pull analysis times by various solvers up into side-by-side columns
    pivot = csv.pivot_table(index=('App', 'Version', 'Fault'), columns='Solver')
    pivot.columns = pivot.columns.droplevel()

    # replace absolute analysis times with UTL-relative times
    pivot['SVPA Over UTL'] = pivot.SVPA / pivot.UTL
    pivot['FSA Over UTL'] = pivot.FSA / pivot.UTL
    del pivot['SVPA']
    del pivot['FSA']
    del pivot['UTL']
    pivot.columns.name = 'Ratio'

    # unpivot and ignore relative times where either involved solver failed to complete
    pivot.reset_index(inplace=True)
    pivot.columns.name = 'Comparison'
    melted = pandas.melt(pivot, id_vars=('App', 'Version', 'Fault'), value_name='Ratio')
    melted.dropna(inplace=True)

    # re-pivot to put FSA/UTL and SVPA/UTL ratios back into side-by-side columns
    del melted['Version']
    del melted['Fault']
    pivot = melted.pivot_table(index='App', columns='Comparison')
    pivot.columns = pivot.columns.droplevel()
    pivot = pivot[pivot.columns.values[::-1]]

    # add LoC column for later sorting
    sizes = pandas.read_csv(argv[1], index_col='App', usecols=('App', 'Mean LoC'))
    pivot = pivot.join(sizes)

    # protect underscores from LaTeX and save for use by paper
    pivot.set_index(pivot.index.str.replace('_', '\\_'), inplace=True)
    pivot.to_csv(stdout)


if __name__ == '__main__':
    main()

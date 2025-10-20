"""

This is a modified version of plot_3vars_savefig.py, which was originally
written by:

E. Wes Bethel, Copyright (C) 2022

Sept. 2025

Description: This code loads a .csv file and creates a 3-variable plot, with various arguments, saving it to the same filename with .png extension.

Inputs:
    filename        the name of the file we read from
    variable        the name of the variable we are plotting, displayed on the y-axis
    suppress_col_1  set this flag if you want to ignore data in column 1 and plot 2 variables instead of 3

Outputs: displays a chart with matplotlib

Dependencies: matplotlib, pandas modules, argparse

"""

import pandas as pd
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(prog='plot.py')
parser.add_argument('filename')
parser.add_argument('-v', '--variable', default='Runtime')
parser.add_argument('-t', '--title', default='PUT A TITLE YOU DUMB FUCKER')
parser.add_argument('-i', '--implementations', default='Basic dgemm,Reference dgemm')
parser.add_argument('-x', '--suffix', default='basic')
args = parser.parse_args()

fname = args.filename
plot_fname = fname.split('.')[0] + f'_{args.suffix}.png'

df = pd.read_csv(fname, comment="#")
print(df)

# var_names = df['Implementation'].tolist()
# print('var_names =', var_names)
impls = args.implementations.split(',')
# print('impls_specified =', impls_specified)
# impls = [v for v in var_names if v in impls_specified]

print("implementations =", impls)

problem_sizes = [int(c) for c in list(df.columns) if c != 'Implementation']
problem_sizes = sorted(problem_sizes)

color_codes = ['r-o', 'b-x', 'g-^', 'm-+', 'c-*', 'y-s', 'k-d']

plt.figure()
plt.title(args.title, wrap=True)
xlocs = [i for i in range(len(problem_sizes))]
plt.xticks(xlocs, problem_sizes)

for idx, impl in enumerate(impls):
    data = []
    for n in problem_sizes:
        data.append(df.loc[df['Implementation'] == impl][str(n)])
    plt.plot(data, color_codes[idx])

print(impls)

#plt.xscale("log")
# plt.yscale("log")

plt.xlabel("Problem Sizes")
plt.ylabel(args.variable)

plt.legend(impls, loc="best")

plt.grid(axis='both')

# save the figure before trying to show the plot
plt.savefig(plot_fname, dpi=300)


plt.show()

# EOF

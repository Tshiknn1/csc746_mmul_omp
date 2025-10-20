"""

Evan Caplinger, (c)2025

Sept. 2025

Description: This code looks at the output from a slurm batch job output file and generates a .csv of runtime or other metrics for the run.

Inputs:
    filename        the name of the output file we read from
    indirect        choose the type of indirect sum we want to read. expect 'indirect_sum' or 'indirect_sum_seed'
    trial           choose the indirect sum trial we want. must be an integer that is found in the output file
    transformation  if you want to calculate a statistic other than runtime, state that here. accepts 'runtime', 'mflops_per_s', 'avg_latency', 'bandwidth', 'pct_bandwidth'
    average         set this flag if you want to also calculate the average of all problem sizes

Outputs: a .csv file with filename <original_filename>_<indirect>_<trial>_<transformation>.csv

Dependencies: argparse

"""

import re
import argparse
import os

PEAK_FLOPS = 3.92e10
PEAK_BANDWIDTH = 2.048e11

TRANSFORM_LUT = {
    'runtime':      lambda n, t: t,
    'mflops':       lambda n, t: 2 * n * n / (t * 1000000),
    'bandwidth':    lambda n, t: (8 * (n * (2 + 2 * n)) / t) / 1e9,
    'pct_bandwidth':lambda n, t: 100 * ((8 * (n * (2 + 2 * n)) / t) / PEAK_BANDWIDTH),
    'avg_latency':  lambda n, t: t / (n * (2 + 2 * n))
}

P_SIZES = [1, 4, 16, 64]

parser = argparse.ArgumentParser(prog='summarize.py')
parser.add_argument('-c', '--categories', default='BLAS,Basic')
parser.add_argument('-d', '--directory', default='no-metrics')
parser.add_argument('-l', '--likwid', default='')
parser.add_argument('-x', '--suffix', default='basic')
# parser.add_argument('indirect')
# parser.add_argument('trial')
parser.add_argument('-t', '--transformation', default='runtime')
parser.add_argument('-a', '--normalize', action='store_true')
args = parser.parse_args()

# if args.transformation not in TRANSFORM_LUT.keys() \
#         and args.transformation != 'speedup':
#     raise Exception('not a recognized transformation')

directory = args.directory
if directory[-1] != '/':
    directory = f'{directory}/'

transformation = args.transformation

data = {}
categories = {
    'BLAS' : 'job-blas.out',
    'Basic': 'job-basic-omp.out',
    'Blocked; B=4': 'job-blocked-omp.out',
    'Blocked; B=16': 'job-blocked-omp.out'
}

ns = []

for category in [c.strip() for c in args.categories.split(',')]:
    fn = categories[category]
    with open(f'{directory}{fn}') as fh:
        print(f'hi from {category}')
        concurrency = None
        blocksize = None
        desired_blocksize = None
        problem_size = None
        if '=' in category:
            desired_blocksize = re.search('B\=(\d+)', category).group(1)
        for line in fh.readlines():
            m = re.search('Hello world, I\'m thread .+ out of (\d+) total threads.', line)
            if m:
                concurrency = int(m.group(1))
                continue
            
            m = re.search('Working on problem size N\=(\d+)', line)
            if m:
                problem_size = int(m.group(1))
                continue
            
            m = re.search(' Working on Block size \= (\d+)', line)
            if m:
                blocksize = m.group(1)
                continue
            
            if transformation in ('speedup', 'runtime'):
                m = re.search('Elapsed time is : (\d+\.\d+)', line)
            elif transformation == 'RETIRED_INSTRUCTIONS':
                m = re.search('RETIRED_INSTRUCTIONS.+\|.+\|\s+(\d+)', line)
            elif transformation == 'L2CACHE':
                m = re.search('L2 accesses.+\|\s+(\d+)', line)
            elif transformation == 'L3CACHE':
                m = re.search('L3_ACCESS_ALL_TYPES.+\|.+\|\s+(\d+)', line)
            if m:
                if blocksize != desired_blocksize:
                    continue

                if args.normalize:
                    if concurrency is None or concurrency > 1: continue
                    data_key = category
                else:   
                    data_key = f'{category}; P={concurrency}'

                if not data_key in data.keys():
                    data[data_key] = {}
                
                value = float(m.group(1))
                if transformation == 'speedup' and int(concurrency) > 1:
                    value = float(data[f'{"=".join(data_key.split("=")[0:-1])}=1'][problem_size]) / value
                print(f"inserting {value} into data[{data_key}][{problem_size}]")

                data[data_key][problem_size] = value
                if args.normalize and data_key != 'BLAS':
                    data[data_key][problem_size] /= data['BLAS'][problem_size]

                if not problem_size in ns: ns.append(problem_size)

print(data)
if args.normalize:
    data['BLAS'] = {k: 1 for k in data['BLAS'].keys()}

to_write = []
to_write.append('Implementation,' + ','.join([f'{i}' for i in sorted(ns)]) + '\n')
for k in sorted(data.keys()):
    v = data[k]
    print(k, data[k])
    to_write.append(f'{k},' + ','.join([f'{v[i]}' for i in sorted(ns)]) + '\n')

fn_out = f'{directory}/{transformation}_{args.suffix}.csv'
with open(fn_out, 'w+') as f:
    f.writelines(to_write)
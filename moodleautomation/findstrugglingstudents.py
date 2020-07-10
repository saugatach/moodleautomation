#!/usr/bin/env python

import argparse
import sys
import glob
import re

import pandas as pd
from tabulate import tabulate

# from moodleautomation.moodleautomation import MoodleAutomation
from moodleautomation import MoodleAutomation


# ---=======================[MAIN MODULE]========================--- #
# usage = "downloadgradebook.py [options]\n" \
#         "-f         Force fetch student IDs [Default=Off]\n" \
#         "-h         Headless mode [Default=On]\n" \
#         "-v         Verbose mode [Default=On]\n" \
#         "With no options it initiates a headless, verbose mode while keeping all older ID data intact\n"
#
# print(usage)

login = False
forcefetchdata = False
forcefetchids = False
headless = False
verbose = False

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--login', help='Stay logged in [Default=Off]. Keep it Off when analysing gradebooks',
                    action='store_true')
parser.add_argument('-f', '--forcefetchdata', help='Force fetch gradebook [Default=Off]', action='store_true')
parser.add_argument('-i', '--forcefetchids', help='Force fetch student IDs [Default=Off]', action='store_true')
parser.add_argument('-o', '--headless', help='Headless mode [Default=Off]', action='store_true')
parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')

args = parser.parse_args()

login = args.login
forcefetchdata = args.forcefetchdata
forcefetchids = args.forcefetchids
headless = args.headless
verbose = args.verbose

print("login:", login)
print("forcefetchdata:", forcefetchdata)
print("forcefetchids:", forcefetchids)
print("headless:", headless)
print("verbose:", verbose)

datadir = '/home/jones/grive/coding/python/moodleautomation/data/'
moodleobj = MoodleAutomation(parent_directory=datadir, login=login, forcefetchdata=forcefetchdata,
                             forcefetchids=forcefetchids, headless=headless, verbose=verbose)

for f in glob.glob(datadir+'PHX*.csv'):
    if len(re.findall(r'PHX(?!.*140)', f)) > 0:
        print(f)
        df = pd.read_csv(f)
        print(tabulate(moodleobj.courseperf(df), headers='keys', tablefmt='psql'))



#!/usr/bin/env python3

import glob
import os
import pickle

import pandas as pd
import numpy as np
import re
import datetime
import time
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt

from tabulate import tabulate


def prettyprint(a, b="="):
    a = "[ " + a + " ]"
    print("# ---"+a.rjust(50+int(len(a)/2), b).ljust(100, b)+"--- #")


def identifyemptygrades():
    for f in glob.glob(PARENT_DIRECTORY + '*.csv'):
        phxcsv = re.findall('MH|QN', f)
        if len(phxcsv) == 0:
            continue

        if verbose:
            prettyprint(os.path.basename(f))

        df = pd.read_csv(f)
        try:
            df.drop(columns=['ID number', 'Campus', 'Program'], inplace=True)
        except KeyError:
            continue

        reviewcols = df.columns[['eview' in x for x in df.columns]]
        df.drop(columns=reviewcols, inplace=True)
        for col in df.columns:
            df1 = df[['First name', 'Last name', 'Email address', col]][((df[col] == '-') & (df['First name'] != 'Student'))]

            # if all students completed their HW then len(df1) = 0
            # If none did then the HW is not open yet and len(df1) = len(df)
            # In either case skip any further processing as there are no grades that need to be set to 0
            if len(df1) == 0 or len(df1) == len(df):
                continue

            print(tabulate(df1, headers='keys', tablefmt='psql'))
            choice = input("To replace the above missing grades with 0 enter 1 otherwise just press enter: ") or 0

            if choice == '1':
                df[col][((df[col] == '-') & (df['First name'] != 'Student'))] = 0
                print(tabulate(df[['First name', 'Last name', col]], headers='keys', tablefmt='psql'))




# ---=======================[MAIN MODULE]========================--- #
verbose = True

# set environ variables
PARENT_DIRECTORY = '/home/jones/grive/coding/python/moodle-automation/data/'
USER_DIR = '/home/jones/.config/selenium'
url = 'https://online.brooklinecollege.edu/'
logincredfile = PARENT_DIRECTORY + 'login.cred'

courseidfile = PARENT_DIRECTORY + 'courseid.csv'
studentidfile = PARENT_DIRECTORY + 'studentid.csv'


identifyemptygrades()


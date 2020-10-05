#!/usr/bin/env python

import os
import glob
import re
import pandas as pd
from tabulate import tabulate
import configparser
import argparse

# the following import is used when package is installed otherwise leave it commented
# from moodleautomation.moodleautomation import MoodleAutomation
from moodleautomation import MoodleAutomation
from gbanalysis import GradebookAnalysis as gba


def emailgenerator(gb, dfsrugglingstudents, dfgradebookdata, assignedhwlist, csvfile, email_template):

    letterfile = os.path.dirname(csvfile) + "/" + 'letter-' + re.sub(r'\.csv', '',  os.path.basename(csvfile)) + '.txt'
    f = open(letterfile, "w")

    for name, email, program in zip(dfsrugglingstudents['Name'], dfsrugglingstudents['Email address'],
                                    dfsrugglingstudents['Program']):
        missedquizzes = gb.getemptyquizzes(dfgradebookdata, assignedhwlist, email)
        missedquizzes = list(map(lambda x: re.sub(r' \(Percentage\)', '', re.sub('External tool:', '', x)),
                                 missedquizzes))
        print(name, missedquizzes)
        letter = gb.generateletter(name, email, missedquizzes, email_template)
        # print(letter)
        f.write(letter)

    # add EOF so the sendbulkemails.py can understand the EOF
    f.write("EOF")

    f.close()


def printdataframe(dftemp):
    print(tabulate(dftemp, headers='keys', tablefmt='psql'))


def main():
    # ---=======================[MAIN MODULE]========================--- #

    # load configurations from settings file using configparser()
    settingsfile = '../settings/settings'

    if os.path.exists(settingsfile):
        config = configparser.ConfigParser()
        config._interpolation = configparser.ExtendedInterpolation()
        config.read(settingsfile)
        paths = config['Paths']

        parent_directory = paths['data_dir'] + "/"
        inputdir = paths['input_dir'] + "/"
        outputdir = paths['output_dir'] + "/"
    else:
        print("No settings file in ../settings/settings. Using default values.")
        parent_directory = '..'
        inputdir = parent_directory + '/data/datainput/'
        outputdir = parent_directory + '/data/dataoutput/'

    # parse command-line arguments using argparse()
    parser = argparse.ArgumentParser(description='Downloads gradebooks from Moodle automatically.')
    parser.add_argument('-l', '--login', help='Stay logged in [Default=Off]. Keep it Off when analysing gradebooks',
                        action='store_true')
    parser.add_argument('-f', '--forcefetchdata', help='Force fetch gradebook [Default=Off]', action='store_true')
    parser.add_argument('-i', '--forcefetchids', help='Force fetch student IDs [Default=Off]', action='store_true')
    parser.add_argument('-o', '--headless', help='Headless mode [Default=Off]', action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')
    parser.add_argument('-m', '--hw-links', help='get hw links', action='store_true')
    parser.add_argument('-t', '--email-template', help='email template file name', type=argparse.FileType('r'))

    args = parser.parse_args()

    login = args.login
    forcefetchdata = args.forcefetchdata
    forcefetchids = args.forcefetchids
    headless = args.headless
    verbose = args.verbose
    hwlinks = args.hw_links
    # if hwlinks option is selected then need to stay logged in
    if hwlinks:
        login = True
    # args.email_template
    if args.email_template is not None:
        email_template = args.email_template.name
    else:
        email_template = inputdir + "emailtemplate1"

    if verbose:
        print("login:", login)
        print("forcefetchdata:", forcefetchdata)
        print("forcefetchids:", forcefetchids)
        print("headless:", headless)
        print("verbose:", verbose)
        print("hw-links:", hwlinks)
        print("Email template file:", email_template)

    print("Data directory:", outputdir)

    if login:
        moodleobj = MoodleAutomation(login=login, forcefetchdata=forcefetchdata, forcefetchids=forcefetchids,
                                 headless=headless, verbose=verbose)
        if hwlinks:
            moodleobj.gethwlinks(verbose)
        print("TEST")

    # analyse gradebook data using class gbanalysis
    gb = gba()

    for csvfile in glob.glob(outputdir+'PHX*.csv'):

        if verbose:
            print(csvfile)

        # load the file containing list of assigned HW
        assignedhwfile = re.sub('PHX', 'HW-links-PHX', csvfile)
        dfassignedhw = pd.read_csv(assignedhwfile)
        assignedhwlist = dfassignedhw[dfassignedhw.columns[0]].to_list()

        dfgradebookdata = pd.read_csv(csvfile)
        dfsrugglingstudents = gb.courseperf(dfgradebookdata, assignedhwlist, verbose=verbose)

        # save data to file
        if len(dfsrugglingstudents) == 0:
            print("No struggling students in this class")
            continue

        dfsrugglingstudents.to_csv(os.path.dirname(csvfile) + '/strugglingstudents-' + os.path.basename(csvfile),
                                   index=False)
        if verbose:
            printdataframe(dfsrugglingstudents.drop(columns=['Email address']))

        emailgenerator(gb, dfsrugglingstudents, dfgradebookdata, assignedhwlist, csvfile, email_template)
        # printmenu(moodleobj, dfsrugglingstudents)


if __name__ == '__main__':
    main()


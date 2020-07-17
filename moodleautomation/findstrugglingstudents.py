#!/usr/bin/env python

import argparse
import os
import glob
import re
import pandas as pd
from tabulate import tabulate
# from moodleautomation.moodleautomation import MoodleAutomation
from moodleautomation import MoodleAutomation


def emailgenerator(cfile):

    letterfile = os.path.dirname(cfile) + "/" + re.sub(r'\.csv', '', os.path.basename(cfile)) + '-letter.txt'
    f = open(letterfile, "w")

    programdirectoremail = {'NUR': 'lenora.spicer@brooklinecollege.edu', 'MLT': 'roger.beckering@brooklinecollege.edu',
                            'MLS': 'roger.beckering@brooklinecollege.edu', 'PTA': 'jane.jackson@brooklinecollege.edu'}

    for name, email, program in zip(dfsrugglingstudents['Name'], dfsrugglingstudents['Email address'],
                                    dfsrugglingstudents['Program']):
        missedquizzes = moodleobj.getemptyquizzes(df, email)
        missedquizzes = list(map(lambda x: re.sub(r' \(Percentage\)', '', re.sub('External tool:', '', x)),
                                 missedquizzes))
        letter = moodleobj.generateletter(name, email, missedquizzes, programdirectoremail[program])
        f.write(letter)

    f.close()


def printmenu():

    while True:
        choice = input("Enter the student# to write (enter to exit): ") or -1
        if choice == -1:
            print("Bye")
            return
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid choice. Try again.")
            continue

        if choice > len(dfsrugglingstudents):
            print("Invalid choice. Try again.")
            continue

        name = dfsrugglingstudents[dfsrugglingstudents.index == choice]['Name'].tolist()[0]
        email = dfsrugglingstudents[dfsrugglingstudents.index == choice]['Email address'].tolist()[0]

        # print(email)
        missedquizzes = moodleobj.getemptyquizzes(df, email)
        missedquizzes = list(map(lambda x: re.sub(r' \(Percentage\)', '', re.sub('External tool:', '', x)),
                                 missedquizzes))

        # print missed quizzes
        print(missedquizzes)

        # generate letter to contact student
        choiceofletter = input("Print letter to student (y|n)? (DEFAULT:y) ") or "y"
        if choiceofletter == "y":
            print(moodleobj.generateletter(name, email, missedquizzes))
            # print("="*50)
            # print(email, "\n")
            # print("Dear", name + ",\n")
            # print("You are missing the following work. Kindly complete your work as soon as possible or request an "
            #       "extension using the 'Assignment Extension Request Form'.\n")
            # print("Only one extension of 2 weeks per assignment is allowed.\n")
            # print("'Assignment Extension Request Form' is posted in the 'Course Summary' section "
            #       "and is accessible from all weeks.\n\n")
            # for n, c in enumerate(missedquizzes):
            #     print('{}. {}'.format(n, c))
            #
            # print("\n\n")
            # print("Kindly let me know if you have any questions or need help with the material.")
            # print("My office hours are every Tuesday at 12pm.")
            # print("\n")
            # print("Best")
            # print("Dr. Chatterjee")
            # print("="*50)


        #
        # dfstu = df[df['Email address'] == email].T
        #
        # print(dfstu)


def printdataframe(dftemp):
    print(tabulate(dftemp, headers='keys', tablefmt='psql'))

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

for csvfile in glob.glob(datadir+'PHX*.csv'):
    # if len(re.findall(r'PHX(?!.*140)', csvfile)) > 0:
    print(csvfile)
    df = pd.read_csv(csvfile)
    dfsrugglingstudents = moodleobj.courseperf(df)
    # save data to file
    dfsrugglingstudents.to_csv(os.path.dirname(csvfile) + '/strugglingstudents-' + os.path.basename(csvfile),
                               index=False)
    printdataframe(dfsrugglingstudents)
    # printmenu()
    emailgenerator(csvfile)

    # if len(re.findall(r'MH140', csvfile)) > 0:
    #     print(csvfile)
    #     df = pd.read_csv(csvfile)
    #     categorypattern = {'hw': 'Week', 'quiz': 'Quiz', 'midterm': 'Midterm \\(Percentage\\)'}
    #     dfsrugglingstudents = moodleobj.courseperf(df, categorypattern=categorypattern)
    #     # save data to file
    #     dfsrugglingstudents.to_csv(os.path.dirname(csvfile) + '/strugglingstudents-' + os.path.basename(csvfile),
    #                                index=False)
    #     printdataframe(dfsrugglingstudents)
    #     # printmenu()
    #     emailgenerator(csvfile)






#!/usr/bin/env python

import argparse
import os
import glob
import re
import pandas as pd
from tabulate import tabulate
# the following import is used when package is installed otherwise leave it commented
# from moodleautomation.moodleautomation import MoodleAutomation
from moodleautomation import MoodleAutomation


def emailgenerator(moodleobj, dfsrugglingstudents, dfgradebookdata, csvfile, email_template):

    letterfile = os.path.dirname(csvfile) + "/" + 'letter-' + re.sub(r'\.csv', '',  os.path.basename(csvfile)) + '.txt'
    f = open(letterfile, "w")

    for name, email, program in zip(dfsrugglingstudents['Name'], dfsrugglingstudents['Email address'],
                                    dfsrugglingstudents['Program']):
        missedquizzes = moodleobj.getemptyquizzes(dfgradebookdata, email)
        missedquizzes = list(map(lambda x: re.sub(r' \(Percentage\)', '', re.sub('External tool:', '', x)),
                                 missedquizzes))
        letter = moodleobj.generateletter(name, email, missedquizzes, email_template)
        # print(letter)
        f.write(letter)

    f.close()


def printmenu(moodleobj, dfsrugglingstudents):

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

        # uncomment to debug
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


def printdataframe(dftemp):
    print(tabulate(dftemp, headers='keys', tablefmt='psql'))


def main():
    # ---=======================[MAIN MODULE]========================--- #
    login = False
    forcefetchdata = False
    forcefetchids = False
    headless = False
    verbose = False
    email_template = ""

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--login', help='Stay logged in [Default=Off]. Keep it Off when analysing gradebooks',
                        action='store_true')
    parser.add_argument('-f', '--forcefetchdata', help='Force fetch gradebook [Default=Off]', action='store_true')
    parser.add_argument('-i', '--forcefetchids', help='Force fetch student IDs [Default=Off]', action='store_true')
    parser.add_argument('-o', '--headless', help='Headless mode [Default=Off]', action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')
    parser.add_argument('-t', '--email-template', help='email template file name', type=argparse.FileType('r'))

    args = parser.parse_args()

    login = args.login
    forcefetchdata = args.forcefetchdata
    forcefetchids = args.forcefetchids
    headless = args.headless
    verbose = args.verbose
    email_template = args.email_template
    datadir = '../data/'

    print("login:", login)
    print("forcefetchdata:", forcefetchdata)
    print("forcefetchids:", forcefetchids)
    print("headless:", headless)
    print("verbose:", verbose)
    print("Data directory:", datadir)
    print("Email template file:", email_template)

    moodleobj = MoodleAutomation(parent_directory=datadir, login=login, forcefetchdata=forcefetchdata,
                                 forcefetchids=forcefetchids, headless=headless, verbose=verbose)

    for csvfile in glob.glob(datadir+'PHX*.csv'):
        print(csvfile)
        dfgradebookdata = pd.read_csv(csvfile)
        dfsrugglingstudents = moodleobj.courseperf(dfgradebookdata)
        # save data to file
        dfsrugglingstudents.to_csv(os.path.dirname(csvfile) + '/strugglingstudents-' + os.path.basename(csvfile),
                                   index=False)
        printdataframe(dfsrugglingstudents)
        emailgenerator(moodleobj, dfsrugglingstudents, dfgradebookdata, csvfile, email_template)
        # printmenu(moodleobj, dfsrugglingstudents)


if __name__ == '__main__':
    main()






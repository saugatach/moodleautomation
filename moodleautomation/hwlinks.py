#!/usr/bin/env python

import argparse
# the following import is used when package is installed otherwise leave it commented
# from moodleautomation.moodleautomation import MoodleAutomation
from moodleautomation import MoodleAutomation


def main():
    # ---=======================[MAIN MODULE]========================--- #
    # parse command-line arguments using argparse()
    parser = argparse.ArgumentParser(description='Create a list of HW links.')
    parser.add_argument('-o', '--headless', help='Headless mode [Default=Off]', action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')

    args = parser.parse_args()
    headless = args.headless
    verbose = args.verbose

    moodleobj = MoodleAutomation(login=True, forcefetchdata=False, forcefetchids=False,
                                 headless=headless, verbose=verbose)

    moodleobj.gethwlinks(verbose)


if __name__ == '__main__':
    main()


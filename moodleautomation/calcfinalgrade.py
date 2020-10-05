#!/usr/bin/env python

from moodleautomation import MoodleAutomation


# ---=======================[MAIN MODULE]========================--- #
def main():
    moodleobj = MoodleAutomation(login=False, forcefetchdata=False, forcefetchids=False, headless=True, verbose=True)

    moodleobj.calcfinalgrade()


if __name__ == '__main__':
    main()

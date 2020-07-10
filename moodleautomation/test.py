#!/usr/bin/env python

import os
import sys

print(sys.path)
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
print(currentdir)
print(parentdir)
print(sys.path)

from moodleautomation.moodleautomation import MoodleAutomation


forcefetchdata = False
forcefetchids = False
headless = False
verbose = False

moodleobj = MoodleAutomation()
moodleobj.check_student_log()
moodleobj.driver.close()

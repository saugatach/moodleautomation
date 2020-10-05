# this is a class file and not executable
import configparser
import os
import re
from functools import reduce
import pandas as pd
import numpy as np
from tabulate import tabulate


def extractnumber(s):
    return re.findall('(\d*,?\d*,?\d*,?\d+,?\d+)', s)[0].replace(',', '')

def containstring(pattern, string):
    """Returns TRUE if the string contains the pattern"""
    return len(re.findall(pattern, string)) > 0

def printdataframe(dftemp):
    print(tabulate(dftemp, headers='keys', tablefmt='psql'))


class GradebookAnalysis:
    
    def __init__(self, parent_directory='../data/', verbose=False):

        if verbose:
            print("Loading module gradebookanalysis")

        # load configurations from settings file
        settingsfile = '../settings/settings'

        if os.path.exists(settingsfile):
            config = configparser.ConfigParser()
            config._interpolation = configparser.ExtendedInterpolation()
            config.read(settingsfile)
            paths = config['Paths']

            self.PARENT_DIRECTORY = paths['data_dir'] + "/"
            self.inputdir = paths['input_dir'] + "/"
            self.outputdir = paths['output_dir'] + "/"
            self.courseidfile = paths['courseidfile']
            self.studentidfile = paths['studentidfile']
        else:
            self.PARENT_DIRECTORY = parent_directory
            self.inputdir = parent_directory + 'datainput/'
            self.outputdir = parent_directory + 'dataoutput/'
            self.courseidfile = self.inputdir + 'courseid.csv'
            self.studentidfile = self.inputdir + 'studentid.csv'

    def courseperf(self, df, assignedhwlist, categorypattern: dict = None, verbose=True):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades for 3 different
        categories ['HW', 'Quiz', 'Midterm']. categorypattern contains the patterns to search for each category
        and needs to be supplied in a dict format as
        {'hw': 'Quiz:HW*', 'quiz': 'Quiz:Quiz*', 'midterm': 'Quiz:Midterm \\(Percentage\\)'}
        :param df:
        :param assignedhwlist:
        :param categorypattern:
        :param verbose:
        :return:
        """

        if categorypattern is None:
            categorypattern = {'hw': ':HW*', 'quiz': ':Quiz \\d+', 'midterm': 'Midterm \\(Percentage\\)'}

        dfslist = []
        for gradeitem, pattern in categorypattern.items():
            dftemp = self.getstrugglingstudents(df, assignedhwlist, gradeitem, pattern, verbose)
            if len(dftemp) > 0:
                dfslist.append(dftemp)

        if len(dfslist) == 0:
            return []

        # recursively merge the dataframe from left to right in the list of dataframes "dfslist"
        dfsrugglingstudents = reduce(lambda x, y: pd.merge(x, y, on='Email address', how='outer'), dfslist)
        dfsrugglingstudents = dfsrugglingstudents.fillna(0)

        # calculate riskscore. This is only a temporary score. Final riskscore will calculated using Overall Grade
        dfsrugglingstudents['riskscore'] = np.round(dfsrugglingstudents.sum(axis=1) / 3, 0)

        # get the current "Overall Grade" for the struggling students as listed in "dfsrugglingstudents"
        df['Name'] = df['First name'] + ' ' + df['Last name']
        dfsrugglingstudentsalldata = dfsrugglingstudents.merge(df, on='Email address', how='inner')

        # df contains the entire gradebook. We do not need all data only specific columns
        # generate the list of columns we want to keep
        templist = dfsrugglingstudents.columns.tolist()
        templist.extend(['Name', 'Program', 'grade'])

        dfsrugglingstudents = dfsrugglingstudentsalldata.rename(columns={'Course total (Percentage)': 'grade'})[
            templist]
        # remove % sign from "Overall Grade" and convert it to float
        dfsrugglingstudents['grade'] = dfsrugglingstudents['grade'].fillna(0).astype(str). \
            map(lambda x: re.sub('-', '0 %', x)).map(lambda x: float(x.rstrip(' %')))

        # rederive the riskscore using the "Overall Grade". Higher "Overall Grade" means lower riskscore
        # so (100 - "Overall Grade") is used instead of "Overall Grade"
        dfsrugglingstudents['riskscore'] = np.round(
            (dfsrugglingstudents['riskscore'] + (100 - dfsrugglingstudents['grade'])) / 2, 0)

        # rearranging columns to put riskscore at the end
        coltoarrange = ['Email address', 'Name', 'Program', 'grade', 'riskscore']
        list(map(
            lambda x: coltoarrange.append(re.findall(r'missed.*', x)[0]) if len(re.findall(r'missed.*', x)) > 0 else '',
            dfsrugglingstudents.columns.tolist()))
        # print(coltoarrange)

        dfsrugglingstudents = dfsrugglingstudents[coltoarrange]

        # replace 'Nursing' with 'Nur' and 'Medical Laboratory Technician' with 'MLT'
        dfsrugglingstudents = dfsrugglingstudents.replace(['Nursing', 'Medical Laboratory Technician',
                                                           'Medical Laboratory Science'], ['NUR', 'MLT', 'MLS'])

        # sort by risk score
        dfsrugglingstudents = dfsrugglingstudents.sort_values(by=['riskscore']).reset_index(drop=True)

        return dfsrugglingstudents

    def getstrugglingstudents(self, df, assignedhwlist, el, s, verbose=True):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades in all columns which belong
        to the grading element s. s is usually a search pattern like (Quiz:HW*). el is the column name for
        emptygradecount. So a typical call would be getstrugglingstudents(df, 'hw', 'Quiz:HW*')
        :param df:
        :param assignedhwlist:
        :param s:
        :param el:
        :param verbose:
        :return:
        """

        # get total number of students
        totstudents = len(df)
        # if over 20% students have already attempted the grading element then anyone who hasn't is falling behind
        # find 80% of class size
        totstudents80percent = int(len(df) * 0.8)
        # if number of empty grades is less than 80% of class size then anyone who hasn't attempted is falling behind

        strugglingstudentlist = []
        assignedquizzes = []

        # select all columns which belong to the grading category s
        # s can be a pattern like (Quiz:HW*) which selects all HW assignments
        mask1 = df.columns.str.contains(s)
        mask2 = np.any([df.columns.str.contains(a+' ') for a in assignedhwlist], axis=0)
        # remove study guides
        mask3 = ~df.columns.str.contains('uide')
        quizlist = df.columns[mask1 & mask2 & mask3].to_list()
        # drop the last quiz as it is just assigned and still open
        quizlist = quizlist[:-1]

        # df.columns.str converts df.columns to a list of strings which is then searched fo a match with regex s
        # the match is generated using contains() which forms a boolean mask
        # which is TRUE when list item matches the pattern
        # that boolean mask is then used to filter only the columns in that category identified by the regex s
        # this is a good piece of code

        # to debug uncomment following line
        # print(quizlist)

        for col in quizlist:
            # select all empty rows and extract student names
            emptygradesdf = df[(df[col] == "-") | (df[col] == "1.00 %")]['Email address']
            noofemptygrades = len(emptygradesdf)

            # check if quiz element is open with at least one attempt
            if noofemptygrades < totstudents:
                assignedquizzes.append(col)

            if noofemptygrades > 0:
                strugglingstudentlist.extend(emptygradesdf.to_list())

        if len(assignedquizzes) == 0:
            if verbose:
                print(s, "is not assigned yet")
            # return empty dataframe
            return pd.DataFrame()

        # generate name of missed grading category from the category name
        missedcol = 'missed' + el
        missedcolpercent = 'missed' + el + 'percent'
        totalcol = 'noof' + el

        # get unique list of student names
        strugglingstudents = set(strugglingstudentlist)

        # counting the number of times a student appears in strugglingstudentlist gives us information about how
        # many grading elements the student has not attempted yet
        dfstrugglingstudents = pd.DataFrame(
            {'Email address': list(strugglingstudents), missedcol: [strugglingstudentlist.count(x)
                                                                    for x in strugglingstudents]})

        # find what percentage of all open quizzes the student hasn't attempted yet
        dfstrugglingstudents[missedcolpercent] = np.round(dfstrugglingstudents[missedcol] / len(assignedquizzes) * 100,
                                                          1)

        # we are interested in the % of missedcol not missedcol itself so we will drop it
        dfstrugglingstudents.drop(columns=[missedcol], inplace=True)

        return dfstrugglingstudents

    def getemptyquizzes(self, df, assignedhwlist, studentemail, categorypattern: dict = None):
        """
        Returns a list of quizzes and assignments from dfcoursedata that the student has not completed.
        The primary key is studentemail. Returns a list of missed quizzes.
        Accepts the Moodle gradebook in percent format as df and searches for empty grades for 3 different
        categories ['HW', 'Quiz', 'Midterm']. categorypattern contains the patterns to search for each category
        and needs to be supplied in a dict format as
        {'hw': 'Quiz:HW*', 'quiz': 'Quiz:Quiz*', 'midterm': 'Quiz:Midterm \\(Percentage\\)'}
        :param df:
        :param assignedhwlist:
        :param studentemail:
        :param categorypattern:
        :return:
        """
        if categorypattern is None:
            categorypattern = {'hw': ':HW*', 'quiz': ':Quiz \\d+', 'midterm': 'Midterm \\(Percentage\\)'}

        missedquizzes = []
        for k, v in categorypattern.items():
            missedquizzesbycategory = self.getemptyquizzesbycategory(df, assignedhwlist, v, studentemail)
            if len(missedquizzesbycategory) > 0:
                missedquizzes.extend(missedquizzesbycategory)

        return missedquizzes

    def getemptyquizzesbycategory(self, df, assignedhwlist, s, studentemail):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades in all columns which belong
        to the grading element s. s is usually a search pattern like (Quiz:HW*). el is the column name for
        emptygradecount. Finally filter for a single student by student email and returns list of missed assignments
        by that student
        :param df:
        :param assignedhwlist:
        :param s:
        :param studentemail:
        :return:
        """

        # # get total number of students
        # totstudents = len(df)
        # # if over 20% students have already attempted the grading element then anyone who hasn't is falling behind
        # # find 80% of class size
        # totstudents80percent = int(len(df) * 0.8)
        # # if number of empty grades is less than 80% of class size then anyone who hasn't attempted is falling behind

        # select all columns which belong to the grading category s
        # s can be a pattern like (Quiz:HW*) which selects all HW assignments
        mask1 = df.columns.str.contains(s)
        mask2 = np.any([df.columns.str.contains(a+' ') for a in assignedhwlist], axis=0)
        # remove study guides
        mask3 = ~df.columns.str.contains('uide')
        quizlist = df.columns[mask1 & mask2 & mask3].to_list()
        # drop the last quiz as it is just assigned and still open
        quizlist = quizlist[:-1]

        missedquizzes = []

        # generate list of columns to iterate through by discarding non-numerical columns
        # quizlist = df.drop(columns=["First name", "Last name", "ID number", "Campus",
        #                                       "Program", "Email address", "Last downloaded from this course"])
        for col in quizlist:
            # select all empty rows and extract student names
            emptygradesdf = df[(df[col] == "-") | (df[col] == "1.00 %")]['Email address']
            noofemptygrades = len(emptygradesdf)

            if noofemptygrades > 0:
                # check if the student didn't attempt this particular assignment
                if emptygradesdf.str.contains(studentemail).any():
                    # to debug uncomment this
                    # print(studentemail, col)
                    missedquizzes.append(col)

        return missedquizzes

    def generateletter(self, name, email, missedquizzes, emailtemplate=None):

        if emailtemplate is None:
            f = open(self.inputdir + 'emailtemplate1', 'r')
        else:
            f = open(emailtemplate, 'r')
            # f = emailtemplate

        lettertext = ''

        with f:
            line = f.readline()

            while line:
                if containstring('\\[email\\]', line):
                    line1 = re.sub('\[email\]', email, line)
                elif containstring('\\[name\\]', line):
                    line1 = re.sub('\[name\]', name.split(" ")[0], line)
                elif containstring('\\[assignments\\]', line):
                    lettertext2 = "   "
                    for n, c in enumerate(missedquizzes, 1):
                        lettertext2 = lettertext2 + str(n) + ". " + str(c) + "\n   "
                    line1 = lettertext2
                else:
                    line1 = line

                lettertext = lettertext + line1

                line = f.readline()

        return lettertext
# this is a class file and not executable

import glob
import os
from functools import reduce

import pandas as pd
import numpy as np
import re
import datetime
import time
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
from selenium import webdriver
from tabulate import tabulate


def sleepy(sleepytime=2):
    time.sleep(sleepytime + np.random.randint(2))


def determine_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    elif score < 60:
        return "F"


def containstring(pattern, string):
    """Returns TRUE if the string contains the pattern"""
    return len(re.findall(pattern, string)) > 0


class MoodleAutomation:
    """This class automates Moodle administration"""

    def __init__(self, parent_directory='../data/',
                 url='https://online.brooklinecollege.edu/',
                 login=False,
                 forcefetchdata=False,
                 forcefetchids=False,
                 headless=False,
                 verbose=False):

        # set environment variables
        logincredfile = parent_directory + 'login.cred'
        courseidfile = parent_directory + 'courseid.csv'
        studentidfile = parent_directory + 'studentid.csv'

        self.PARENT_DIRECTORY = parent_directory

        # if forcefetchdata and/or forcefetchids is True then start ChromeDriver to begin data download
        if forcefetchdata or forcefetchids:
            # load driver
            self.driver = self.load_webdriver(url, headless=headless, incognito=True, verbose=verbose)
            # log into website
            self.login(logincredfile)

            if os.path.exists(courseidfile) and not forcefetchids:
                self.df_courseid = pd.read_csv(courseidfile)
            else:
                self.df_courseid = self.get_course_id(verbose)

            if os.path.exists(studentidfile) and not forcefetchids:
                self.df_studentid = pd.read_csv(studentidfile)
            else:
                self.df_studentid = self.getallid(self.df_courseid, verbose)

            # delete existing gradebooks and download latest version
            for f in glob.glob(self.PARENT_DIRECTORY + 'PHX*.csv'):
                print("Deleting ", f)
                os.remove(f)

            self.get_gradebooks(self.df_courseid, verbose)
            self.renamefiles()

            # if user doesn't want to stay logged in then close webdriver after downlaoding the data
            if not login:
                self.driver.close()
                if verbose:
                    print("ChromeDriver Shutdown")
        # if user just wants to stay logged in but not download data then open webdriver and remain logged in
        elif login:
            # load driver and stay logged in
            self.driver = self.load_webdriver(url, headless=headless, incognito=True, verbose=verbose)
            # log into website
            self.login(logincredfile)

        # calcfinalgrade()
        # identifyemptygrades()
        # check_student_log()

    # ---==================[reusable code [start]]===================--- #

    def ff(self, elementname, classname):
        return self.driver.find_elements_by_xpath('//' + elementname + '[@class="' + classname + '"]')

    def get_element(self, cl, el='div'):
        try:
            button = self.driver.find_element_by_xpath('//' + el + '[@class="' + cl + '"]')
        except:
            return False

        return button

    # -----------------------[Open ChromeDriver]------------------------ #
    def load_webdriver(self, url, headless=False, incognito=False, verbose=True):
        """
        Loads ChromeDriver with ChromeOptions[--incognito, download.default_directory, user-agent]
        :return:
        """

        # use an user-agent to mimic real user
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/60.0.3112.50 Safari/537.36'

        # set default download directory and user0agent with ChromeOptions
        chromeoptions = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.PARENT_DIRECTORY}

        chromeoptions.add_experimental_option("prefs", prefs)
        chromeoptions.add_argument('user-agent={0}'.format(user_agent))

        if incognito:
            chromeoptions.add_argument("--incognito")
        if headless:
            chromeoptions.add_argument('--headless')

        driver1 = webdriver.Chrome(options=chromeoptions)
        driver1.get(url)
        if verbose:
            print("Opening ", url)
        sleepy()  # Let the user actually see something!
        return driver1

    # -----------------------------[Login]------------------------------ #
    def login(self, logincredfile):
        """
        Logs into the website using stored credentials form the file login.cred
        :param logincredfile:
        :return:
        """

        # BEGIN MANUAL LOGIN
        # login credentials from file to avoid exposing them in code
        if os.path.exists(logincredfile):
            f = open(logincredfile, "r")
            uname = f.readline().strip()
            pwd = f.readline().strip()
            f.close()
        else:
            print("login.cred is missing. Exiting.")
            exit(-1)

        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")

        username.click()
        username.send_keys(uname)
        sleepy()

        password.click()
        password.send_keys(pwd)
        sleepy()

        submit = self.driver.find_element_by_xpath('//input[@type="submit"]')
        submit.click()
        sleepy()

        # saving session
        # save_cookie(driver, cookiesfile)

        if self.driver.current_url == 'https://online.brooklinecollege.edu/':
            print('Successfull login')
        else:
            print('Login failed. Exiting.')
            exit(-1)

        sleepy(5)

    # ---------------------------[End Login]---------------------------- #
    # ---===================[reusable code [end]]====================--- #

    def get_course_id(self, verbose=True):
        """
        Gets all course names and course IDs and returns a data frame of matched coursename and courseid
        :return df_courseid:
        """
        if verbose:
            print("Getting course IDs")

        # check if sidebar is open or not. If the sidebar is not open then click it open
        sidebar = self.ff('button', 'btn nav-link float-sm-left mr-1 btn-light bg-gray')[0]

        if sidebar.get_attribute('aria-expanded') == 'false':
            sidebar.click()

        courses = []
        courseid = []
        courselink_elements = []
        drawer_elements = self.ff("a", "list-group-item list-group-item-action ")  # space at end of class is required
        for c in drawer_elements:
            phx = re.findall(r'PHX', c.text)
            if phx:
                courses.append(c.text)
                courseid.append(re.findall(r'\d+', c.get_attribute('href'))[0])
                courselink_elements.append(c)

        # coursenames = list(map(lambda x: re.findall(r'.{7}$', x)[0], courses))
        coursenames = courses
        df_courseid = pd.DataFrame({'coursenames': coursenames, 'courseid': courseid})

        df_courseid.drop_duplicates(inplace=True)

        return df_courseid

    def get_student_id_from_gradebook(self, courseid, verbose=True):
        """
        Gets student names and ids from the gradebook from a course using the courseid
        :param courseid:
        :param verbose:
        :return:
        """
        # url_gradebook_setup = 'https://online.brooklinecollege.edu/grade/edit/tree/index.php?id=' + str(courseid)
        url_gradebook_report = 'https://online.brooklinecollege.edu/grade/report/grader/index.php?id=' + str(courseid)

        self.driver.get(url_gradebook_report)

        if verbose:
            print(url_gradebook_report)

        sleepy()
        htmlsource = self.driver.page_source
        soup = bs(htmlsource, 'lxml')

        # Check for "Recalculating grades" page
        try:
            # driver.find_element_by_xpath('//h2[@id="yui_3_17_2_1_1587151625236_24"]')
            # If continue button is available then click it
            continuebtn = self.driver.find_element_by_xpath('//button[contains(text(),"Continue")]')
            continuebtn.click()
            sleepy()
        except:
            d = 0
        # table = soup.findAll('table')[0]

        nameslist = list(soup.findAll('a', class_="username"))
        stunames = nameslist[:int(len(nameslist) / 2)]
        student_ids = list(map(lambda x: re.findall(r'id=(\d+)', str(x))[0], stunames))
        student_names = list(map(lambda x: re.findall(r'>(.*)<', str(x))[0], stunames))
        student_emails = list(map(lambda x: x.text, soup.findAll('td', class_='userfield useremail cell c2')))

        df_studentid = pd.DataFrame(
            {'studentid': student_ids, 'student_name': student_names, 'student_email': student_emails})

        return df_studentid

    def getallid(self, df_cid1, verbose=True):
        """
        Iterate over course ids and obtain a list of student enrolled in each course. Returns a dataframe of all student
        :param df_cid1:
        :param verbose:
        :return:
        """

        if verbose:
            print("Getting student IDs")

        # dfstudentid = pd.DataFrame( {'studentid': [], 'student_name': [], 'student_email': []})
        studentslist = []

        # need to set 'courseid' as index otherwise cannot access the row using 'courseid'
        df_cid = df_cid1.set_index('courseid')

        # df_courseid = df_cid.set_index('courseid')
        df_cid['students'] = ''  # [''] * len(df_courseid)

        for courseid in df_cid.index:
            df_studentid_temp = self.get_student_id_from_gradebook(courseid, verbose=verbose)

            # add student list to each course
            stuids = set(df_studentid_temp['studentid'])
            df_cid['students'].loc[courseid] = stuids

            # create a column courseid which contains the course id of every course the student is enrolled in
            df_studentid_temp['courseid'] = courseid

            # merge all student dataframe to make one big dataframe for student IDs
            studentslist.append(df_studentid_temp)
            # df3 = df_studentid_temp.merge(dfstudentid, on=['studentid', 'student_name', 'student_email'], how='outer')
            # dfstudentid = df3

        #         print(df3)

        dfstudentid = pd.concat(studentslist).drop_duplicates()

        student_database = self.PARENT_DIRECTORY + 'studentid.csv'
        dfstudentid.set_index('studentid').to_csv(student_database)

        course_database = self.PARENT_DIRECTORY + 'courseid.csv'
        df_cid.to_csv(course_database)

        return dfstudentid

    def get_gradebooks(self, df_courseid, verbose=True):
        """
        Downloads gradebooks from all courses
        :param df_courseid:
        :param verbose:
        :return:
        """

        # cycle through the courses
        courses = df_courseid['coursenames']
        courseid = df_courseid['courseid']

        for cname, cid in zip(courses, courseid):
            url = 'https://online.brooklinecollege.edu/grade/export/txt/index.php?id=' + str(cid)
            if verbose:
                print("Getting " + cname)
            self.driver.get(url)
            if verbose:
                print(url)
            sleepy()

            # Click the 'Export format options' to select Percentage instead of Real
            dropdownmenus = self.driver.find_elements_by_xpath('//a[@class="fheader"]')
            for dd in dropdownmenus:
                if dd.text == 'Export format options' and dd.get_attribute('aria-expanded') == 'false':
                    print('Export format options was closed. Clicking it to open')
                    dd.click()
                    sleepy(0)

            # uncheck the real and check the percent checkbox
            real_checkbox = self.driver.find_element_by_id("id_display_real")
            if real_checkbox.is_selected():
                real_checkbox.click()

            percent_checkbox = self.driver.find_element_by_id("id_display_percentage")
            if not percent_checkbox.is_selected():
                percent_checkbox.click()
                sleepy(0)

            submit = self.driver.find_elements_by_xpath('//input[@type="submit"]')
            for x in submit:
                if x.get_attribute("value") == 'Download':
                    x.click()
                    sleepy(5)

            if verbose:
                print("CSV file saved")

    def renamefiles(self):
        """code to rename downloaded Moodle gradebook files"""

        for f in glob.glob(self.PARENT_DIRECTORY + 'PHX*.csv'):
            # phxcsv = re.findall('PHX', f)
            # if len(phxcsv) == 0:
            #     continue

            # fname = re.sub('PHX\..*?\.| Grades.*d', '', f)
            fname = re.sub('Grades.*d', '', f)
            os.rename(f, fname)

    def identifyemptygrades(self, verbose=True):
        for f in glob.glob(self.PARENT_DIRECTORY + '*.csv'):
            phxcsv = re.findall('MH|QN', f)
            if len(phxcsv) == 0:
                continue

            if verbose:
                print("Reading", f)

            df = pd.read_csv(f)
            try:
                df.drop(columns=['ID number', 'Campus', 'Program', 'Email address'], inplace=True)
            except KeyError:
                continue

            reviewcols = df.columns[['eview' in x for x in df.columns]]
            df.drop(columns=reviewcols, inplace=True)
            for col in df.columns:
                df1 = df[['First name', 'Last name', col]][((df[col] == '-') & (df['First name'] != 'Student'))]
                if len(df1) == 0:
                    continue
                print(f, '=' * 80)
                print(tabulate(df1, headers='keys', tablefmt='psql'))
                input("Fix the above missing grades and press enter")

    def calcfinalgrade(self, verbose=True):
        for f in glob.glob(self.PARENT_DIRECTORY + '*.csv'):
            phxcsv = re.findall('[^final].*(MH|QN)', f)
            if len(phxcsv) == 0:
                continue

            if verbose:
                print("Reading", f)

            df = pd.read_csv(f)
            try:
                df.drop(columns=['ID number', 'Campus', 'Program', 'Email address'], inplace=True)
            except KeyError:
                continue
            df = df[(df["Course total (Percentage)"] != '-')].dropna()
            df['finalgrade'] = list(
                map(lambda x: np.round(float(re.findall(r'\d+.\d+', x)[0]), 0), df["Course total (Percentage)"]))
            df = df[['First name', 'Last name', 'finalgrade']][(df['First name'] != 'Student')]
            df['lettergrade'] = list(map(determine_grade, df['finalgrade']))

            cid = re.findall(r'/.*/(.*)\.csv', f)[0]
            fname = self.PARENT_DIRECTORY + 'final_grades_' + str(cid)
            df.to_csv(fname + '.csv', index=False)

            print(cid)
            # print(tabulate(df, headers='keys', tablefmt='psql'))
            # print(df.groupby('lettergrade')['lettergrade'].nunique())
            freq = df['lettergrade'].value_counts().sort_index()
            # print(freq)
            plt.bar(freq.index, freq)
            plt.xlabel("Grades")
            plt.ylabel("Freq")
            plt.title(cid)
            # plt.show()
            plt.savefig(fname + '.png')
            plt.close()

    def check_student_log(self, verbose=True):
        sname = input("Enter student name: ")

        if verbose:
            print("Reading", self.PARENT_DIRECTORY + 'studentid.csv')
            print("Reading", self.PARENT_DIRECTORY + 'courseid.csv')

        dfstudentid = pd.read_csv(self.PARENT_DIRECTORY + 'studentid.csv')
        dfcourseid = pd.read_csv(self.PARENT_DIRECTORY + 'courseid.csv')

        dfstudent = dfstudentid[[sname in name for name in dfstudentid['student_name']]]
        print(dfstudent)

        if len(dfstudent) > 1:
            sid = input("Select student ID: ")
        elif len(dfstudent) == 1:
            sid = int(dfstudent['studentid'])
        else:
            print("Student not found.")
            return -1

        sid = str(sid)

        dfcourse = dfcourseid[[sid in students for students in dfcourseid['students']]]
        if len(dfcourse) > 1:
            print(dfcourse)
            cid = input("Select course ID: ")
        else:
            cid = int(dfcourse['courseid'])
        cid = str(cid)

        suspicionlevel = self.check_logs(sid, cid)

        if suspicionlevel < 0:  # Error occured
            print("Error")
            return -1

        if suspicionlevel == 1:
            print("Something smells fishy .... Check logs")
        else:
            print("Clean")

    def check_logs(self, studentid, courseid, verbose=True):
        log_url = 'https://online.brooklinecollege.edu/report/log/user.php?id={0}&course={1}&mode=today'. \
            format(studentid, courseid)
        self.driver.get(log_url)
        if verbose:
            print(log_url)
        sleepy(4)

        df_temp = pd.read_html(self.driver.page_source)
        log = []

        if len(df_temp) > 1:
            df_log = df_temp[1]
        else:
            return -1  # ERROR

        log = list(df_log['Event name'])
        if 'Quiz attempt started' in log:
            endindex = log.index('Quiz attempt started') + 1
            if 'Quiz attempt submitted' in log:
                startindex = log.index('Quiz attempt submitted')
                logstatus = 2
            else:
                startindex = 0
                logstatus = 2
        else:
            logstatus = -1
            return logstatus

        eventsbetweenstartandend = log[startindex:endindex][::-1]
        if len(eventsbetweenstartandend) > 5:
            suspicionlevel = 1
        else:
            suspicionlevel = 0

        return suspicionlevel

    def getstrugglingstudents(self, df, el, s):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades in all columns which belong
        to the grading element s. s is usually a search pattern like (Quiz:HW*). el is the column name for
        emptygradecount. So a typical call would be getstrugglingstudents(df, 'hw', 'Quiz:HW*')
        :param df:
        :param s:
        :param el:
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
        quizlist = df.columns[df.columns.str.contains(s)].to_list()
        # df.columns.str converts df.columns to a list of strings which is then searched fo a match with regex s
        # the match is generated using contains() which forms a boolean mask
        # which is TRUE when list item matches the pattern
        # that boolean mask is then used to filter only the columns in that category identified by the regex s
        # this is a good piece of code

        # to debug uncomment following line
        # print(quizlist)

        for col in quizlist:
            # select all empty rows and extract student names
            emptygradesdf = df[df[col] == "-"]['Email address']
            noofemptygrades = len(emptygradesdf)

            # check if quiz element is open with at least one attempt
            if noofemptygrades < totstudents:
                assignedquizzes.append(col)

            if noofemptygrades > 0:
                # check if quiz element has at least 20% attempt
                # students who haven't attempted yet are behind
                if noofemptygrades < totstudents80percent:
                    strugglingstudentlist.extend(emptygradesdf.to_list())

        if len(assignedquizzes) == 0:
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

    def courseperf(self, df, categorypattern: dict = None):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades for 3 different
        categories ['HW', 'Quiz', 'Midterm']. categorypattern contains the patterns to search for each category
        and needs to be supplied in a dict format as
        {'hw': 'Quiz:HW*', 'quiz': 'Quiz:Quiz*', 'midterm': 'Quiz:Midterm \\(Percentage\\)'}
        :param df:
        :param categorypattern:
        :return:
        """

        if categorypattern is None:
            categorypattern = {'hw': 'HW*', 'quiz': ':Quiz \\d+', 'midterm': 'Midterm \\(Percentage\\)'}

        dfslist = []
        for k, v in categorypattern.items():
            dftemp = self.getstrugglingstudents(df, k, v)
            if len(dftemp) > 0:
                dfslist.append(dftemp)

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
        dfsrugglingstudents = dfsrugglingstudents.sort_values(by=['riskscore']).reset_index()

        return dfsrugglingstudents

    def getemptyquizzes(self, df, studentemail, categorypattern: dict = None):
        """
        Returns a list of quizzes and assignments from dfcoursedata that the student has not completed.
        The primary key is studentemail. Returns a list of missed quizzes.
        Accepts the Moodle gradebook in percent format as df and searches for empty grades for 3 different
        categories ['HW', 'Quiz', 'Midterm']. categorypattern contains the patterns to search for each category
        and needs to be supplied in a dict format as
        {'hw': 'Quiz:HW*', 'quiz': 'Quiz:Quiz*', 'midterm': 'Quiz:Midterm \\(Percentage\\)'}
        :param df:
        :param studentemail:
        :param categorypattern:
        :return:
        """
        if categorypattern is None:
            categorypattern = {'hw': 'HW*', 'quiz': ':Quiz \\d+', 'midterm': 'Midterm \\(Percentage\\)'}

        missedquizzes = []
        for k, v in categorypattern.items():
            missedquizzesbycategory = self.getemptyquizzesbycategory(df, v, studentemail)
            if len(missedquizzesbycategory) > 0:
                missedquizzes.extend(missedquizzesbycategory)

        return missedquizzes

    def getemptyquizzesbycategory(self, df, s, studentemail):
        """
        Accepts the Moodle gradebook in percent format as df and searches for empty grades in all columns which belong
        to the grading element s. s is usually a search pattern like (Quiz:HW*). el is the column name for
        emptygradecount. Finally filter for a single student by student email and returns list of missed assignments
        by that student
        :param df:
        :param s:
        :param studentemail:
        :return:
        """

        # get total number of students
        totstudents = len(df)
        # if over 20% students have already attempted the grading element then anyone who hasn't is falling behind
        # find 80% of class size
        totstudents80percent = int(len(df) * 0.8)
        # if number of empty grades is less than 80% of class size then anyone who hasn't attempted is falling behind

        # select all columns which belong to the grading category s
        # s can be a pattern like (Quiz:HW*) which selects all HW assignments
        quizlist = df.columns[df.columns.str.contains(s)].to_list()

        missedquizzes = []
        assignedquizzes = []

        # generate list of columns to iterate through by discarding non-numerical columns
        # quizlist = df.drop(columns=["First name", "Last name", "ID number", "Campus",
        #                                       "Program", "Email address", "Last downloaded from this course"])
        for col in quizlist:
            # select all empty rows and extract student names
            emptygradesdf = df[df[col] == "-"]['Email address']
            noofemptygrades = len(emptygradesdf)

            # check if quiz element is open with at least one attempt
            if noofemptygrades < totstudents:
                assignedquizzes.append(col)

            if noofemptygrades > 0:
                # check if quiz element has at least 20% attempt
                # students who haven't attempted yet are behind
                if noofemptygrades < totstudents80percent:
                    # check if the student didn't attempt this particular assignment
                    if emptygradesdf.str.contains(studentemail).any():
                        missedquizzes.append(col)

        # missedquizzesdict = {'missedquizzes': missedquizzes, 'assignedquizzes': assignedquizzes}
        return missedquizzes

    def generateletter(self, name, email, missedquizzes, emailtemplate=None):

        if emailtemplate is None:
            emailtemplate = open(self.PARENT_DIRECTORY + 'emailtemplate1', 'r')
            f = emailtemplate

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

        #
        #
        #
        #
        #
        # lettertext1 = "Hi " + name.split(" ")[0] + ",\n\n" + \
        #               "You are missing the following work. Kindly complete your work as soon as \npossible or " \
        #               "request an extension using the 'Assignment Extension Request Form'.\n\nOnly one extension " \
        #               "of 1 week per assignment is allowed.\n\n'Assignment Extension Request Form' is posted in the " \
        #               "'Course Summary' section \nand is accessible from all weeks.\n\n\n"
        #
        # lettertext2 = "   "
        # for n, c in enumerate(missedquizzes, 1):
        #     lettertext2 = lettertext2 + str(n) + ". " + str(c) + "\n   "
        #
        # lettertext3 = "\n\nKindly let me know if you have any questions or need help with the material.\n" \
        #               "My office hours are every Tuesday at 12pm.\n\n" \
        #               "Best\nDr. Chatterjee\n\n"
        #
        # letter = "=" * 70 + "\n" + email + "\n\n" + \
        #          lettertext1 + lettertext2 + lettertext3
        #
        # return letter
        #
        #
        #
        #

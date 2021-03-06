# this is a class file and not executable

import glob
import os
from functools import reduce
import pandas as pd
import numpy as np
import re
import time
from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
from selenium import webdriver
from tabulate import tabulate
import configparser


def sleepy(sleepytime=2):
    time.sleep(sleepytime + np.random.randint(2))


def extractnumber(s):
    return re.findall('(\d*,?\d*,?\d*,?\d+,?\d+)', s)[0].replace(',', '')


def printdataframe(dftemp):
    print(tabulate(dftemp, headers='keys', tablefmt='psql'))


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
                 headless=True,
                 verbose=False):

        if verbose:
            print("Loading module MoodleAutomation")

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
            logincredfile = paths['login_cred']
            self.courseidfile = paths['courseidfile']
            self.studentidfile = paths['studentidfile']
        else:
            self.PARENT_DIRECTORY = parent_directory
            self.inputdir = parent_directory + 'datainput/'
            self.outputdir = parent_directory + 'dataoutput/'
            logincredfile = self.inputdir + 'login.cred'
            self.courseidfile = self.inputdir + 'courseid.csv'
            self.studentidfile = self.inputdir + 'studentid.csv'

        # if forcefetchdata and/or forcefetchids is True then start ChromeDriver to begin data download
        if forcefetchdata or forcefetchids:
            # load driver
            self.driver = self.load_webdriver(url, headless=headless, incognito=True, verbose=verbose)
            # log into website
            self.login(logincredfile)

            if os.path.exists(self.courseidfile) and not forcefetchids:
                self.df_courseid = pd.read_csv(self.courseidfile)
            else:
                self.df_courseid = self.get_course_id(verbose)

            if os.path.exists(self.studentidfile) and not forcefetchids:
                self.df_studentid = pd.read_csv(self.studentidfile)
            else:
                self.df_studentid = self.getallid(self.df_courseid, verbose)

            # delete existing gradebooks and download latest version
            for f in glob.glob(self.outputdir + 'PHX*.csv'):
                print("Deleting ", f)
                os.remove(f)

            self.get_gradebooks(self.df_courseid, verbose)
            self.renamefiles(verbose=verbose)

            # if user doesn't want to stay logged in then close webdriver after downloading the data
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
        prefs = {"download.default_directory": self.outputdir}

        chromeoptions.add_experimental_option("prefs", prefs)
        chromeoptions.add_argument('user-agent={0}'.format(user_agent))

        if incognito:
            chromeoptions.add_argument("--incognito")
            if verbose:
                print("Initiating incognito mode")

        if headless:
            chromeoptions.add_argument('--headless')
            if verbose:
                print("Initiating headless mode")

        if verbose:
            print("Download dir:", self.outputdir)

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

        dfstudentid.set_index('studentid').to_csv(self.studentidfile)
        df_cid.to_csv(self.courseidfile)

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
                    sleepy()

            # uncheck the real and check the percent checkbox
            real_checkbox = self.driver.find_element_by_id("id_display_real")
            if real_checkbox.is_selected():
                real_checkbox.click()

            percent_checkbox = self.driver.find_element_by_id("id_display_percentage")
            if not percent_checkbox.is_selected():
                percent_checkbox.click()
                if verbose:
                    print("Selecting percentage for grade format")
                sleepy()

            submit = self.driver.find_elements_by_xpath('//input[@type="submit"]')
            for x in submit:
                if x.get_attribute("value") == 'Download':
                    x.click()
                    if verbose:
                        print("Clicking download button")
                    sleepy(30)

            if verbose:
                print("CSV file saved")

    def renamefiles(self, verbose=True):
        """code to rename downloaded Moodle gradebook files"""

        if verbose:
            print("Renaming files in the directory:", self.outputdir)

        for f in glob.glob(self.outputdir + 'PHX*.csv'):
            # phxcsv = re.findall('PHX', f)
            # if len(phxcsv) == 0:
            #     continue

            # fname = re.sub('PHX\..*?\.| Grades.*d', '', f)
            fname = re.sub('Grades.*d', '', f)
            fname = re.sub(' *\.csv', '.csv', fname)

            if verbose:
                print("Renaming", f, "---->", fname)

            os.rename(f, fname)

    def identifyemptygrades(self, verbose=True):
        for f in glob.glob(self.outputdir + '*.csv'):
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
                df1 = df[['First name', 'Last name', col]]
                [((df[col] == "-") | (df[col] == "1.00 %") & (df['First name'] != 'Student'))]
                if len(df1) == 0:
                    continue
                print(f, '=' * 80)
                printdataframe(df1)
                input("Fix the above missing grades and press enter")

    def calcfinalgrade(self, verbose=True):
        for f in glob.glob(self.outputdir + 'PHX*.csv'):
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
            df = df[(df["Course total (Percentage)"] != "-")].dropna()
            df['finalgrade'] = list(
                map(lambda x: np.round(float(re.findall(r'\d+.\d+', x)[0]), 0), df["Course total (Percentage)"]))
            df = df[['First name', 'Last name', 'finalgrade']][(df['First name'] != 'Student')]
            df.sort_values(by=['finalgrade'], inplace=True)
            df['lettergrade'] = list(map(determine_grade, df['finalgrade']))

            print("Success rate: {0:4.2f}%".format(len(df[df['finalgrade'] < 70])/len(df)*100))

            cid = re.findall(r'/.*/(.*)\.csv', f)[0]
            fname = self.outputdir + 'final_grades_' + str(cid)
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

            if verbose:
                printdataframe(df)

    def check_student_log(self, verbose=True):
        sname = input("Enter student name: ")

        if verbose:
            print("Reading", self.studentidfile)
            print("Reading", self.courseidfile)

        dfstudentid = pd.read_csv(self.studentidfile)
        dfcourseid = pd.read_csv(self.courseidfile)

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

    def gethwlinks(self, verbose):

        if verbose:
            print("Getting links to override page for HW assignments")

        # load course ids
        df_courseid = pd.read_csv(self.courseidfile)

        # cycle through the courses
        courses = df_courseid['coursenames']
        courseid = df_courseid['courseid']

        for cname, cid in zip(courses, courseid):
            url = 'https://online.brooklinecollege.edu/grade/edit/tree/index.php?id=' + str(cid)
            if verbose:
                print("Getting " + cname)
            self.driver.get(url)
            if verbose:
                print(url)
            sleepy()

            pagetext = self.driver.page_source
            pagesoup = bs(pagetext, "lxml")

            # get a list of HW which are not assigned yet
            # filter the list of all links by the class "dimmed"
            gradeitems = pagesoup.findAll('tr', class_="dimmed_text")
            dimmedlist = []
            for gr in gradeitems:
                x = gr.findAll('a', class_='gradeitemheader')[0]
                # print(x.text)
                dimmedlist.append(x.text)

            # extract all links in grade setup
            gradeitems = pagesoup.findAll('a', class_="gradeitemheader")
            namelist = []
            linklist = []
            for x in gradeitems:
                namelist.append(x.text)
                link = 'https://online.brooklinecollege.edu/mod/quiz/overrides.php?cmid=' \
                       + extractnumber(x['href']) + '&mode=user'
                linklist.append(link)

            # create a a dataframe from the HW names and the links to them
            dflinkstohw = pd.DataFrame({cname: namelist, 'link': linklist})
            # printdataframe(dflinkstohw)

            # only get the dataframe row which do not appear in the "dimmed" list (non assigned)
            dflinkstohw = dflinkstohw[~dflinkstohw[cname].isin(dimmedlist)]
            # printdataframe(dflinkstohw)

            # remove links to non-graded items
            dflinkstohw = dflinkstohw[~dflinkstohw[cname].str.contains('Non-graded')]
            dflinkstohw = dflinkstohw[~dflinkstohw[cname].str.contains('Guide')]
            dflinkstohw = dflinkstohw[~dflinkstohw[cname].str.contains('Survey')]
            dflinkstohw = dflinkstohw[~dflinkstohw[cname].str.contains('Ungraded')]
            # printdataframe(dflinkstohw)

            # save to file to used by a separate program
            dflinkstohw.to_csv(self.outputdir + 'HW-links-' + cname + '.csv', index=False)

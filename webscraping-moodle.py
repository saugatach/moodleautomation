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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tabulate import tabulate


# ---==================[reusable code [start]]===================--- #
def sleepy(sleepytime=2):
    time.sleep(sleepytime + np.random.randint(2))


def ff(elementname, classname):
    return driver.find_elements_by_xpath('//' + elementname + '[@class="' + classname + '"]')


def save_cookie(driver, f):
    with open(f, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)


def load_cookie(driver, f):
    if os.path.exists(f):
        with open(f, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                print(cookie)
                driver.add_cookie(cookie)
        return True
    else:
        return False


def get_element(cl, el='div'):
    try:
        button = driver.find_element_by_xpath('//' + el + '[@class="' + cl + '"]')
    except:
        return False

    return button


# -----------------------[Open ChromeDriver]------------------------ #
def load_webdriver(url, headless=False, incognito=False):
    """
    Loads ChromeDriver with ChromeOptions[--incognito, download.default_directory, user-agent]
    :return:
    """

    # use an user-agent to mimic real user
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/60.0.3112.50 Safari/537.36'

    # set default download directory and user0agent with ChromeOptions
    chromeoptions = webdriver.ChromeOptions()
    prefs = {"download.default_directory": PARENT_DIRECTORY}

    chromeoptions.add_experimental_option("prefs", prefs)
    chromeoptions.add_argument('user-data-dir={0}'.format(USER_DIR))
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
def login(driver, url_login, logincredfile, cookiesfile):
    """
    Logs into the website using stored credentials form the file login.cred
    :param driver:
    :param url_login:
    :param logincredfile:
    :param cookiesfile:
    :return:
    """

    # check if cookies exist
    # if load_cookie(driver, cookiesfile):
    #     print("Cookies found")
    #     print("Getting", url_login)
    #     driver.get(url_login)
    #     print("Cookies working ... proceeding")
    #     return
    # else:
    #     print("No cookies found")

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

    username = driver.find_element_by_name("username")
    password = driver.find_element_by_name("password")

    username.click()
    username.send_keys(uname)
    sleepy()

    password.click()
    password.send_keys(pwd)
    sleepy()

    submit = driver.find_element_by_xpath('//input[@type="submit"]')
    submit.click()
    sleepy()

    # saving session
    # save_cookie(driver, cookiesfile)

    if verbose:
        print('Successfull login')

    sleepy(5)
# ---------------------------[End Login]---------------------------- #
# ---===================[reusable code [end]]====================--- #

def getCourseID():
    # check if sidebar is open or not. If the sidebar is not open then click it open
    sidebar = ff('button', 'btn nav-link float-sm-left mr-1 btn-light bg-gray')[0]

    if sidebar.get_attribute('aria-expanded') == 'false':
        sidebar.click()

    courses = []
    courseid = []
    courselink_elements = []
    drawer_elements = ff("a", "list-group-item list-group-item-action ")  # the space at the end of class is required
    for c in drawer_elements:
        PHX = re.findall(r'PHX', c.text)
        if PHX:
            courses.append(c.text)
            courseid.append(re.findall(r'\d+', c.get_attribute('href'))[0])
            courselink_elements.append(c)

    # coursenames = list(map(lambda x: re.findall(r'.{7}$', x)[0], courses))
    coursenames = courses
    df_courseid = pd.DataFrame({'coursenames': coursenames, 'courseid': courseid})

    df_courseid.drop_duplicates(inplace=True)

    return df_courseid


def getStudentIDfromGradebook(courseid):
    # url_gradebook_setup = 'https://online.brooklinecollege.edu/grade/edit/tree/index.php?id=' + str(courseid)
    url_gradebook_report = 'https://online.brooklinecollege.edu/grade/report/grader/index.php?id=' + str(courseid)

    driver.get(url_gradebook_report)

    if verbose:
        print(url_gradebook_report)

    sleepy()
    htmlsource = driver.page_source
    soup = bs(htmlsource, 'lxml')

    # Check for "Recalculating grades" page
    try:
        # driver.find_element_by_xpath('//h2[@id="yui_3_17_2_1_1587151625236_24"]')
        # If continue button is available then click it
        continuebtn = driver.find_element_by_xpath('//button[contains(text(),"Continue")]')
        continuebtn.click()
        sleepy()
    except:
        d = 0
    # table = soup.findAll('table')[0]

    nameslist = list(soup.findAll('a', class_="username"))
    stunames = nameslist[:int(len(nameslist)/2)]
    student_ids = list(map(lambda x: re.findall(r'id=(\d+)', str(x))[0], stunames))
    student_names = list(map(lambda x: re.findall(r'>(.*)<', str(x))[0], stunames))
    student_emails = list(map(lambda x: x.text, soup.findAll('td', class_='userfield useremail cell c2')))

    df_studentid = pd.DataFrame(
        {'studentid': student_ids, 'student_name': student_names, 'student_email': student_emails})

    return df_studentid


def getallID(df_cid1):
    df_studentid = pd.DataFrame(
        {'studentid': [], 'student_name': [], 'student_email': []})

    # need to set 'courseid' as index otherwise cannot access the row using 'courseid'
    df_cid = df_cid1.set_index('courseid')

    # df_courseid = df_cid.set_index('courseid')
    df_cid['students'] = ''  # [''] * len(df_courseid)

    for courseid in df_cid.index:
        df_studentid_temp = getStudentIDfromGradebook(courseid)

        # add student list to each course
        stuids = set(df_studentid_temp['studentid'])
        df_cid['students'].loc[courseid] = stuids

        # merge all student dataframe to make one big dataframe for student IDs
        df3 = df_studentid_temp.merge(df_studentid, on=['studentid', 'student_name', 'student_email'], how='outer')

        df_studentid = df3

    #         print(df3)

    student_database = PARENT_DIRECTORY + 'studentid.csv'
    df_studentid.set_index('studentid').to_csv(student_database)

    course_database = PARENT_DIRECTORY + 'courseid.csv'
    df_cid.to_csv(course_database)

    return df_studentid


def check_logs(studentid, courseid):
    log_url = 'https://online.brooklinecollege.edu/report/log/user.php?id={0}&course={1}&mode=today'.format(studentid,
                                                                                                            courseid)
    driver.get(log_url)
    if verbose:
        print(log_url)
    sleepy(4)


    df_temp = pd.read_html(driver.page_source)
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
        logstatus = 0

    eventsbetweenstartandend = log[startindex:endindex][::-1]
    if len(eventsbetweenstartandend) > 5:
        suspicionlevel = 1
    else:
        suspicionlevel = 0

    return suspicionlevel


def getGradebooks(df_courseid):

    # cycle through the courses

    courses = df_courseid['coursenames']
    courseid = df_courseid['courseid']

    for cname, cid in zip(courses, courseid):
        url = 'https://online.brooklinecollege.edu/grade/export/txt/index.php?id=' + str(cid)
        if verbose:
            print("Getting " + cname)
            print(url)
        driver.get(url)
        if verbose:
            print(url)
        sleepy()

        # Click the 'Export format options' to select Percentage instead of Real
        dropdownmenus = driver.find_elements_by_xpath('//a[@class="fheader"]')
        for dd in dropdownmenus:
            if dd.text == 'Export format options' and dd.get_attribute('aria-expanded') == 'false':
                print('Export format options was closed. Clicking it to open')
                dd.click()
                sleepy(0)

        # uncheck the real and check the precent checkbox

        real_checkbox = driver.find_element_by_id("id_display_real")
        if real_checkbox.is_selected():
            real_checkbox.click()

        percent_checkbox = driver.find_element_by_id("id_display_percentage")
        if not percent_checkbox.is_selected():
            percent_checkbox.click()
            sleepy(0)

        submit = driver.find_elements_by_xpath('//input[@type="submit"]')
        for x in submit:
            if x.get_attribute("value") == 'Download':
                x.click()
                sleepy()

        if verbose:
            print("CSV file saved")


def renamefiles():
    """code to rename downloaded Moodle gradebook files"""

    for f in glob.glob(PARENT_DIRECTORY + '*.csv'):
        phxcsv = re.findall('PHX', f)
        if len(phxcsv) == 0:
            continue

        # fname = re.sub('PHX\..*?\.| Grades.*d', '', f)
        fname = re.sub('Grades.*d', '', f)
        os.rename(f, fname)


def identifyemptygrades():
    for f in glob.glob(PARENT_DIRECTORY + '*.csv'):
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
            print(f, '='*80)
            print(tabulate(df1, headers='keys', tablefmt='psql'))
            input("Fix the above missing grades and press enter")


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


def calcfinalgrade():
    for f in glob.glob(PARENT_DIRECTORY + '*.csv'):
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
            map(lambda x: np.round(float(re.findall('\d+.\d+', x)[0]), 0), df["Course total (Percentage)"]))
        df = df[['First name', 'Last name', 'finalgrade']][(df['First name'] != 'Student')]
        df['lettergrade'] = list(map(determine_grade, df['finalgrade']))

        cid = re.findall('\/.*\/(.*)\.csv', f)[0]
        fname = PARENT_DIRECTORY + 'final_grades_' + str(cid)
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

def check_student_log():
    sname = input("Enter student name: ")

    if verbose:
        print("Reading", PARENT_DIRECTORY + 'studentid.csv')
        print("Reading", PARENT_DIRECTORY + 'courseid.csv')

    dfstudentid = pd.read_csv(PARENT_DIRECTORY + 'studentid.csv')
    dfcourseid = pd.read_csv(PARENT_DIRECTORY + 'courseid.csv')

    dfstudent = dfstudentid[[sname in name for name in dfstudentid['student_name']]]
    print(dfstudent)
    if len(dfstudent) > 1:
        sid = input("Select student ID")
    else:
        sid = int(dfstudent['studentid'])
    sid = str(sid)

    dfcourse = dfcourseid[[sid in students for students in dfcourseid['students']]]
    if len(dfcourse)>1:
        print(dfcourse)
        cid = input("Select course ID")
    else:
        cid = int(dfcourse['courseid'])
    cid = str(cid)

    suspicionlevel = check_logs(sid, cid)

    if suspicionlevel < 0:  # Error occured
        print("Error")

    if suspicionlevel == 1:
        print("Something smells fishy .... Check logs")
    else:
        print("Clean")


# ---========================MAIN MODULE=========================---
verbose = True

# set environ variables
PARENT_DIRECTORY = '/home/jones/grive/coding/python/moodle-automation/data/'
USER_DIR = '/home/jones/.config/selenium'
url = 'https://online.brooklinecollege.edu/'
logincredfile = PARENT_DIRECTORY + 'login.cred'
cookiesfile = PARENT_DIRECTORY + 'cookies-bc'
url_login = 'https://online.brooklinecollege.edu/my/'

courseidfile = PARENT_DIRECTORY + 'courseid.csv'
studentidfile = PARENT_DIRECTORY + 'studentid.csv'


# load driver
driver = load_webdriver(url, headless=True, incognito=True)
# log into website
login(driver, url_login, logincredfile, cookiesfile)
driver.maximize_window()

if os.path.exists(courseidfile):
    df_courseid = pd.read_csv(courseidfile)
else:
    df_courseid = getCourseID()

if os.path.exists(studentidfile):
    df_studentid = pd.read_csv(studentidfile)
else:
    df_studentid = getallID(df_courseid)

getGradebooks(df_courseid)
renamefiles()
# calcfinalgrade()
#
driver.close()
if verbose:
    print("ChromeDriver Shutdown")

# identifyemptygrades()
# check_student_log()

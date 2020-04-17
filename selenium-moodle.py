#!/usr/bin/env python3
import os

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


def sleepy(sleepytime=2):
    time.sleep(sleepytime + np.random.randint(2))


def ff(elementname, classname):
    return driver.find_elements_by_xpath('//' + elementname + '[@class="' + classname + '"]')


# ---==================[reusable code [start]]===================--- #
# -----------------------[Open ChromeDriver]------------------------ #
def load_webdriver():
    """
    Loads ChromeDriver with ChromeOptions[--incognito, download.default_directory, user-agent]
    :return:
    """

    # use an user-agent to mimic real user
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/60.0.3112.50 Safari/537.36'

    # set default download directory and user0agent with ChromeOptions
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"download.default_directory": PARENT_DIRECTORY}
    chromeOptions.add_experimental_option("prefs", prefs)
    chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument('user-agent={0}'.format(user_agent))
    # chromeOptions.add_argument('--no-sandbox')
    # chromeOptions.add_argument('--window-size=1420,1080')
    # chromeOptions.add_argument('--headless')
    # chromeOptions.add_argument('--disable-gpu')
    # chromeOptions.add_argument("--allow-insecure-localhost")

    driver = webdriver.Chrome(options=chromeOptions)
    if verbose:
        print("Opening ", url)

    driver.get(url)
    time.sleep(2)  # Let the user actually see something!
    return driver


# -----------------------------[Login]------------------------------ #
def login():
    """
    Logs into the website using stored credentials form the file login.cred
    :param driver:
    :param verbose:
    :return:
    """

    # login credentials from file to avoid exposing them in code
    file = PARENT_DIRECTORY + 'login.cred'
    if os.path.exists(file):
        f = open(file, "r")
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

    coursenames = list(map(lambda x: re.findall(r'.{7}$', x)[0], courses))
    df_courseid = pd.DataFrame({'coursenames': coursenames, 'courseid': courseid})

    df_courseid.drop_duplicates(inplace=True)

    return df_courseid


def getStudentIDfromGradebook(courseid):
    url_gradebook_setup = 'https://online.brooklinecollege.edu/grade/edit/tree/index.php?id=' + str(courseid)
    url_gradebook_report = 'https://online.brooklinecollege.edu/grade/report/grader/index.php?id=' + str(courseid)

    driver.get(url_gradebook_report)
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

    nameslist = list(set(soup.findAll('a', class_="username")))
    student_ids = list(map(lambda x: re.findall(r'id=(\d+)', str(x))[0], nameslist))
    student_names = list(map(lambda x: re.findall(r'>(.*)<', str(x))[0], nameslist))
    student_emails = list(map(lambda x: x.text, soup.findAll('td', class_='userfield useremail cell c2')))

    df_studentid = pd.DataFrame(
        {'student_id': student_ids, 'student_name': student_names, 'student_email': student_emails})

    return df_studentid


def getallID(df_cid):
    df_studentid = pd.DataFrame(
        {'student_id': [], 'student_name': [], 'student_email': []})

    # need to set 'courseid' as index otherwise cannot access the row using 'courseid'
    df_cid.set_index('courseid', inplace=True)

    # df_courseid = df_cid.set_index('courseid')
    df_cid['students'] = ''  # [''] * len(df_courseid)

    for courseid in df_cid.index:
        df_studentid_temp = getStudentIDfromGradebook(courseid)

        # add student list to each course
        stuids = set(df_studentid_temp['student_id'])
        df_cid['students'].loc[courseid] = stuids

        # merge all student dataframe to make one big dataframe for student IDs
        df3 = df_studentid_temp.merge(df_studentid, on=['student_id', 'student_name', 'student_email'], how='outer')

        df_studentid = df3

    #         print(df3)

    student_database = PARENT_DIRECTORY + 'student_id.csv'
    df_studentid.set_index('student_id').to_csv(student_database)

    course_database = PARENT_DIRECTORY + 'course_id.csv'
    df_cid.to_csv(course_database)

    return df_studentid


def check_logs(studentid, courseid):
    log_url = 'https://online.brooklinecollege.edu/report/log/user.php?id={0}&course={1}&mode=today'.format(studentid,
                                                                                                            courseid)

    driver.get(log_url)
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

    if suspicionlevel < 0:  # Error occured
        print("Error")

    if suspicionlevel == 1:
        print("Something smells fishy .... Check logs")
    else:
        print("Clean")

    return suspicionlevel


def getGradebooks(df_courseid):

    # cycle through the courses

    courses = df_courseid['coursenames']
    courseid = df_courseid['courseid']

    for cname, cid in zip(courses, courseid):
        url = 'https://online.brooklinecollege.edu/grade/export/txt/index.php?id=' + cid
        if verbose:
            print("Getting " + cname)
            print(url)
        driver.get(url)
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

# ---========================MAIN MODULE=========================---

verbose = True

# set default download directory
PARENT_DIRECTORY = '/home/jones/grive/coding/python/moodle-proctoring/data/'
url = 'https://online.brooklinecollege.edu/'

driver = load_webdriver()
login()
df_courseid = getCourseID()
df_studentid = getallID(df_courseid)
getGradebooks(df_courseid)
# suspicionlevel = check_logs(sid, cid)


driver.close()
if verbose:
    print("ChromeDriver Shutdown")

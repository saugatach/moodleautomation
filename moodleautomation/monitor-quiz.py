#!/usr/bin/env python3
import glob
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
from tabulate import tabulate


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

    driver1 = webdriver.Chrome(options=chromeOptions)
    driver1.get(url)
    if verbose:
        print("Opening ", url)
    sleepy()  # Let the user actually see something!
    return driver1


# -----------------------------[Login]------------------------------ #
def login(driver):
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


# ---========================MAIN MODULE=========================---
verbose = True

# set default download directory
PARENT_DIRECTORY = '/home/jones/grive/coding/python/moodle-automation/data/'
# PARENT_DIRECTORY = './'
url = 'https://online.brooklinecollege.edu/'

driver = load_webdriver()
login(driver)
# df_courseid = getCourseID()
# df_studentid = getallID(df_courseid)
# getGradebooks(df_courseid)
# renamefiles()
# calcfinalgrade()
#


# identifyemptygrades()
check_student_log()
driver.close()
if verbose:
    print("ChromeDriver Shutdown")
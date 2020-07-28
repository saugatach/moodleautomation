#!/usr/bin/env python

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import time
import glob
import re
import numpy as np


def sleepy(sleepytime=2):
    time.sleep(sleepytime + np.random.randint(2))


def sendmessage(s, emailto, emailsubject, emailmsg):
    msg = MIMEMultipart()
    msg['From'] = "saugata.chatterjee@brooklinecollege.edu"
    msg['To'] = emailto
    msg['Subject'] = emailsubject
    msg.attach(MIMEText(emailmsg, 'plain'))
    s.send_message(msg)
    del msg


def main():
    parent_directory = '../data/'
    logincredfile = parent_directory + 'login.cred'
    # BEGIN MANUAL LOGIN
    # login credentials from file to avoid exposing them in code
    if os.path.exists(logincredfile):
        f = open(logincredfile, "r")
        uname = f.readline().strip()
        pwd = f.readline().strip()
        f.close()

    # set up the SMTP server
    s = smtplib.SMTP(host="smtp-mail.outlook.com", port=587)
    s.starttls()
    print("Logging in")
    s.login(uname, pwd)

    emailto = ""
    emailmsg = ""
    counter = 0

    # For each contact, send the email:
    for emailfile in glob.glob(parent_directory+'*.txt'):

        coursename = re.sub(' ', '', re.sub(r'-letter.txt', '', os.path.basename(emailfile)).strip(" "))
        emailsubject = "[" + coursename + "] " + "Unattempted assignments"

        print(emailsubject, "\n")

        with open(emailfile, 'r') as f:
            line = f.readline()
            while line:

                if line == '='*70+'\n':
                    # print(line)
                    sleepy()
                    # send email and start constructing the next message
                    if emailto != "":
                        print(counter, "Sending email to", emailto)
                        # print(emailmsg)
                        print('-'*70, "\n")
                        # uncomment following line to test
                        # emailto = "saugata.ch@gmail.com"
                        sendmessage(s, emailto, emailsubject, emailmsg)
                        counter = counter + 1
                    elif counter > 0:
                        print("Email address not present. Exiting")
                        exit(-1)

                    # after sending the previous email start a new email message
                    emailto = f.readline()
                    emailmsg = ""
                else:
                    emailmsg = emailmsg + line
                line = f.readline()
                # if counter > 1:
                #     break

    s.quit()


if __name__ == '__main__':
    main()

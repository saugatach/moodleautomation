#!/usr/bin/env python

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import time
import glob
import re
import pandas as pd
import numpy as np
import datetime as dt
import configparser
import argparse
import getpass

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


def createmessage(dfsentemails, s, emailsentfilecsv, counter, emailto, emailsubject, emailmsg, verbose, dryrun):

    # send email and start constructing the next message
    if emailto != "":
        emailto = emailto.strip()
        # check if emailto has already being emailed today. Do not spam
        if len(dfsentemails) > 0:
            # print(dfsentemails)
            if dfsentemails["email"].str.contains(emailto).any():
                try:
                    datelastemailed = pd.to_datetime(dfsentemails[(dfsentemails["email"] == emailto)]['date'].iloc[-1])
                    datelastemailed = datelastemailed.date()
                    if datelastemailed == dt.date.today():
                        print("Already sent email to: ", emailto)
                        print("Skipping")
                        print('-' * 70)
                    return
                except:
                    d = 1

        if dryrun:
            print(counter, "Sending email to", emailto)
            # add email to dataframe and save to file in case of crash
            # dfsentemails.loc[len(dfsentemails)] = [dt.date.today(), emailto]
            # dfsentemails.to_csv(emailsentfilecsv, index=False)
            if verbose:
                print(emailsubject)
                print(emailmsg)
            print('-' * 70)
        else:
            sleepy()

            sendmessage(s, emailto, emailsubject, emailmsg)
            # add email to dataframe and save to file in case of crash
            dfsentemails.loc[len(dfsentemails)] = [dt.date.today(), emailto]
            dfsentemails.to_csv(emailsentfilecsv, index=False)
            if verbose:
                print(counter, "Sending email to", emailto)
                print(emailsubject)
                # print(emailmsg)
                print('-' * 70, "\n")
    elif counter > 0:
        print("Email address not present. Exiting")
        exit(-1)


def getlogininfo():
    uname = input("Enter username: ") or "X"
    if uname == "X":
        print("Username skipped. Exiting.")
        exit(-1)
    try:
        pwd = getpass.getpass()
    except Exception as error:
        print("Password skipped. Exiting.")
        exit(-2)

    return [uname, pwd]


def main():
    
    # load configurations from settings file using configparser()
    settingsfile = '../settings/settings'

    if os.path.exists(settingsfile):
        config = configparser.ConfigParser()
        config._interpolation = configparser.ExtendedInterpolation()
        config.read(settingsfile)
        paths = config['Paths']

        outputdir = paths['output_dir'] + "/"
        emailsentfilecsv = paths['emailsentfile']
        logincredfile = paths['login_cred']
    else:
        print("No settings file in ../settings/settings. Using default values.")
        parent_directory = ".."
        inputdir = parent_directory + 'datainput/'
        outputdir = parent_directory + 'dataoutput/'
        logincredfile = inputdir + 'login.cred'

    if os.path.exists(emailsentfilecsv):
        dfsentemails = pd.read_csv(emailsentfilecsv)
    else:
        dfsentemails = pd.DataFrame({'date': [], 'email': []})

    print("Saving data to: ", emailsentfilecsv)

    # parse command-line arguments using argparse()
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')
    parser.add_argument('-l', '--login', help='Enter login info manually [Default=Off]', action='store_true')
    parser.add_argument('-n', '--dryrun', help='Dry run (not send emails)', action='store_true')

    args = parser.parse_args()

    verbose = args.verbose
    login = args.login
    dryrun = args.dryrun

    if dryrun:
        print("In dryrun the [emailsentfilecsv] is not created so that multiples runs shows data output.")

    # BEGIN MANUAL LOGIN
    # login credentials from file to avoid exposing them in code
    if not login:
        if os.path.exists(logincredfile):
            f = open(logincredfile, "r")
            uname = f.readline().strip()
            pwd = f.readline().strip()
            f.close()
        else:
            print('Login credentials file not found. Enter it manually.')
            uname, pwd = getlogininfo()
    else:
        uname, pwd = getlogininfo()

    # set up the SMTP server
    s = smtplib.SMTP(host="smtp-mail.outlook.com", port=587)
    s.starttls()
    print("Logging in")
    s.login(uname, pwd)

    emailto = ""
    emailmsg = ""
    counter = 0

    # For each contact, send the email:
    for emailfile in glob.glob(outputdir+'*.txt'):

        coursename = re.sub(' ', '', re.sub(r'letter-', '', re.sub(r'.txt', '', os.path.basename(emailfile)).strip(" ")))
        emailsubject = "[" + coursename + "] " + "Unattempted assignments"

        if verbose:
            print('+' * 80, "\n")
            print(emailsubject, "\n")

        with open(emailfile, 'r') as f:
            line = f.readline()

            while line:

                if line == '='*70+'\n':
                    createmessage(dfsentemails, s, emailsentfilecsv, counter, emailto, emailsubject, emailmsg,
                                                 verbose, dryrun)
                    # after sending the previous email start a new email message
                    counter = counter + 1
                    emailto = f.readline()
                    emailmsg = ""

                elif line == "EOF":
                    createmessage(dfsentemails, s, emailsentfilecsv, counter, emailto, emailsubject, emailmsg,
                                                 verbose, dryrun)

                    # after sending the previous email start a new email message
                    counter = 0
                    emailto = ""
                    emailmsg = ""

                else:
                    emailmsg = emailmsg + line

                line = f.readline()
                # print(line)

                # if counter > 1:
                #     break

    s.quit()


if __name__ == '__main__':
    main()

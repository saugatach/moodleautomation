
# Moodleautomation

Automates many repetitive Moodle operations.

## INSTALLATION

No installation candidate as of now. Working on it. The modes need to be run directly after unzipping the package. It has some dependencies on selenium, pandas, and chromedriver. The chromedriver version must match the chrome installed in the system. The process of installation is kept manual for now to allow greater flexibility in terms of installing the correct chromedriver version. If chromedriver is not available, the analysis modules can be used by manually downloading the gradebooks in the `data` folder.

## DESCRIPTION

The package consists of several different modules which perform different functions. Currently it do the following. 

 1. Download all gradebooks (downloadgradebook.py)
 2. Finds incomplete assignments (findstrugglingstudents.py)
 3. Makes a list of struggling students and assigns them risk scores (findstrugglingstudents.py)
 4. Creates email template to send to students (findstrugglingstudents.py)
 5. Automatic emails struggling students to remind them to complete their missed assignments (sendbulkemails.py)

## FILES
The main functionality is provided by a class file called `moodleautomation.py`. The rest of the modules do specific tasks.

	moodleautomation.py				Class file providing most of the 
									functionality
	downloadgradebook.py			Downloads all gradebooks
	findstrugglingstudents.py		Finds incomplete assignments,
									makes a list of struggling students 
									and assigns them risk scores, and
									creates email template to send to students
	sendbulkemails.py				Send emails automatically to students

## OPTIONS

### Options for downloadgradebook.py

	-h,		--help				show this help message and exit
	-l,		--login				Stay logged in [Default=Off]. Keep it off when
								analysing gradebooks
	-f,		--forcefetchdata	Force fetch gradebook [Default=Off]
	-i,		--forcefetchids		Force fetch student IDs [Default=Off]
	-o,		--headless			Headless mode [Default=Off]
	-v,		--verbose			Verbose mode [Default=Off]

#### USAGE
Common usage is to clear out the old gradebooks and re-download them. For that we need to enable `--forcefetchdata` option . 

	downloadgradebook.py -fov

### Options for findstrugglingstudents.py

	-h,		--help				show this help message and exit
	-l,		--login				Stay logged in [Default=Off]. Keep it off when
								analysing gradebooks
	-f,		--forcefetchdata	Force fetch gradebook [Default=Off]
	-i,		--forcefetchids		Force fetch student IDs [Default=Off]
	-o,		--headless			Headless mode [Default=Off]
	-v,		--verbose			Verbose mode [Default=Off]
	-t,		--email-template	email template file name

#### USAGE
`findstrugglingstudents.py` automatically invokes the same functionality as `downloadgradebook.py`. So there is no need to run `downloadgradebook.py` before `findstrugglingstudents.py`. `downloadgradebook.py` is run only when we need to download the gradebooks to manually inspect them.

Common usage is to clear out the old gradebooks and re-download them. For that we need to enable `--forcefetchdata` option .

	findstrugglingstudents.py -fov
If `downloadgradebook.py` is run before `findstrugglingstudents.py` then running `findstrugglingstudents.py` without any option will work as well.

## SCRIPTS

The `scripts` folder contains scripts that can be used to clean out the old gradebooks from the data folder.

## UML diagrams

```mermaid graph LR
A(moodleautomation) --> B(downloadgradebook)
B(downloadgradebook) --> C[../data/gradebook.csv]
B(downloadgradebook) --> D[../data/studentid.csv]
B(downloadgradebook) --> E[../data/courseid.csv]
C[../data/gradebook.csv] --> F(findstrugglingstudents)
F(findstrugglingstudents) --> H[../data/struggling.csv]
F(findstrugglingstudents) --> I[../data/emails.csv]
G[../data/emailtemplate] --> I[../data/emails.csv]
I[../data/emails.csv] --> K(sendbulkemails)
```

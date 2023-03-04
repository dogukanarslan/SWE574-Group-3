# SWE573 Fall 2022 - Project
This repository is a project for the class named SWE573 - Software Development Practices in Boğaziçi University Software Engineering Deparment.

# The URLs:
Project URL: http://44.201.174.233:8000/<br/>
Swagger Documentation: http://44.201.174.233:8000/swagger/<br/>
Admin Panel: http://44.201.174.233:8000/admin/

## To run with docker at local machine:

After you started the docker and be sure about docker is running then you can simply
run these commands :

docker-compose build<br/>
then<br/>
docker-compose up<br/>
in the first time you start the project.

"docker-compose up" will create postgresql database and migrate all migrations file in the first time.
After that only docker-compose up will be sufficient unless any database or
library change occurs. If this will be the case you should also run "docker-compose build"
before "docker-compose up". Sometimes build does not install libraries that you need
if this is the case, you need to run docker-compose down first then build then up.

In this case the backend will be served in http://0.0.0.0:8000/


## To reach api documentation, visit "localhost:8000/swagger"
## To reach django admin panel interface, visit "localhost:8000/admin":
You should createsuperuser to use django admin panel, with the command "python manage.py createsuperuser"

# Project Management
In this project, GitHub Issues of this repository will be used for project management. There will be a set of issues about the works of the project.

## Labels
Labels are used for describing the issue.

There will be a set of labels for this purpose. Up to now, there are 14 labels. 

### Description of the Labels

Three of the labels are about the type of the works that will be developed: <br>
1. **Type: Task** -  Something is a task that may contains new features, new developments etc.
2. **Type: Bug** - Something is already developed but has a bug, so the type of it is bug.
3. **Type: Epic** - Something needs more than one development in it, and there will be a group of tasks for this issue.

Two of the labels are about the prioritization of the works that will be developed. 

1. **Priority: Major** - Somethings has a high priority and it needs to be developed as soon as possible.
2. **Priority: Minor** - Something has a low priority compared to others.

Four of the labels are about the status of progress of an issue:

1. **Status: To-Do** - Something is in backlog and it is waiting for development.
2. **Status: Development** - Something is in progress.
3. **Status: QA** - If there is a need for testing, the issue should be go to QA process. Something is in testing.
4. **Status: Done** - Something is completed.

Four of the labels are about the resolution criteria of an issue:

1. **Resolution: Fixed** - Something is bug fixed and resolved.
2. **Resolution: Won't Fixed** - Something is not fixed and is cancelled.
3. **Resolution: Done** - Something is done and completed.
4. **Resolution: Won't Do** - Something is not done and it is cancelled.

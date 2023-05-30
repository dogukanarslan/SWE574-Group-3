# SWE574 Spring 2023
This repository is a project for the class named SWE574 - Software Development as a Team in Boğaziçi University Software Engineering Department.

### URL
Project URL: http://13.48.149.195:8000/<br/>
Swagger Documentation: http://13.48.149.195:8000/swagger/<br/>
Admin Panel: http://13.48.149.195:8000/admin/

### Team
- Afize Özcan
- Cansın Cömert
- Doğukan Arslan
- Ege Pekgenç
- İlayda Kurt
- Mehmet Emre Berk
- Miray İyidoğan
- Samed Torun

### Run with Docker

After you started the docker and be sure about docker is running then you can simply
run these commands :

`docker-compose build` then` docker-compose up` in the first time you start the project.

`docker-compose up` will create PostgreSQL database and migrate all migrations file in the first time.
After that only docker-compose up will be sufficient unless any database or
library change occurs. If this will be the case you should also run `docker-compose build`
before `docker-compose up`. Sometimes build does not install libraries that you need
if this is the case, you need to run `docker-compose down` first then build then up.

In this case the backend will be served in http://0.0.0.0:8000/

You should createsuperuser to use django admin panel, with the command "python manage.py createsuperuser"

### Project Management
In this project, GitHub Issues of this repository will be used for project management. There will be a set of issues about the works of the project.

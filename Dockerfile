FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN apk update
RUN apk add --update  --no-cache postgresql-client jpeg-dev libffi-dev gcc vim
# jpeg-dev, musl-dev, zlib & zlib-dev is required for Pillow (image upload)
RUN apk add --update  --no-cache --virtual .tmp-build-deps \
      libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
RUN pip install -r /requirements.txt
RUN apk del .tmp-build-deps

EXPOSE 8000
ENV LC_ALL=en_US.UTF8

# create-empty-folder
RUN mkdir /app
# make-default-workingdirectory
WORKDIR /app
# copy-local-app-into-docker-folder-app
COPY ./app /app

RUN mkdir -p /app/media
RUN mkdir -p /app/static
# User create for security and -D means running application only!
RUN adduser -D user
# give ownership to any subdir of /vol/
RUN chown -R user:user /app/
# owner can do anything and others can read & execute from directory
# RUN chown -R 755 /vol/web/
RUN chmod 755 /app/
USER user

FROM centos:latest
MAINTAINER Aaron Dunlop

RUN yum update -y && yum clean all

RUN yum -y install epel-release && yum clean all
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm

RUN yum -y install git && yum clean all
RUN yum -y install vim && yum clean all
RUN yum -y install python36u && yum clean all
RUN yum -y install python36u-devel && yum clean all
RUN yum -y install python36u-pip && yum clean all
RUN yum -y install gcc && yum clean all

RUN pip3.6 install virtualenv
RUN python3.6 -m venv venv
RUN mkdir -p /data/comicbetter /data/comics /var/lib/comicbetter /var/log/comicbetter
ARG expire_after=never
RUN git clone https://github.com/aarondunlop/comicbetter-server /var/lib/comicbetter/
RUN cp /var/lib/comicbetter/etc/config.yml.master /var/lib/comicbetter/etc/config.yml
RUN cp /var/lib/comicbetter/etc/flask.yml.master /var/lib/comicbetter/etc/flask.yml
VOLUME [ '/data/comicbetter/image' '/data/comicbetter/read' '/data/comics' '/var/log/comicbetter' ]


ENV WORKON_HOME "/var/lib/comicbetter/env"
ENV VIRTUAL_ENV "/var/lib/comicbetter/env"
ENV PATH ${VIRTUAL_ENV}/bin:${PATH}
WORKDIR "/var/lib/comicbetter"

RUN python3.6 -m venv venv
RUN . venv/bin/activate
RUN LC_CTYPE="en_US.UTF-8" pip3.6 install --requirement '/var/lib/comicbetter/requirements.txt'

ENTRYPOINT python3.6 -u '/var/lib/comicbetter/run.py'
EXPOSE 58008

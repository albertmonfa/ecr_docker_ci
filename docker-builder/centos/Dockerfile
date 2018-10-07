FROM centos:7

MAINTAINER Albert Monfà


RUN yum -y update && \
    yum -y install epel-release && \
    yum -y install python2 python2-pip python-virtualenv ruby ruby-devel make \
	gcc libffi-devel rpm-build && \
    pip install -U pip setuptools virtualenv && \
    pip install boto3 ConfigArgParse docker-py PyYAML jsonschema six && \
    gem install fpm

CMD ["/bin/bash"]

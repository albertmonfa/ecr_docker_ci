
FROM debian:jessie

MAINTAINER Albert Monfà

RUN apt-get update && \
    apt-get -y install python python-pip python-virtualenv build-essential \
	make gcc libyaml-dev python-dev rubygems-integration ruby ruby-dev && \
 	pip install -U pip setuptools virtualenv && \
    pip install boto3 ConfigArgParse docker-py PyYAML jsonschema six && \
    gem install fpm

CMD ["/bin/bash"]

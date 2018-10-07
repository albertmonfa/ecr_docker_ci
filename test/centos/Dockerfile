FROM centos:7

MAINTAINER Albert Monfà

COPY test_app.rpm /root/test_app.rpm

RUN yum -y update && \
    yum -y install python && \
    rpm -ivh /root/test_app.rpm 

CMD ["/bin/sh"]

FROM debian:jessie

MAINTAINER Albert Monfà

COPY test_app.deb /root/test_app.deb

RUN apt-get update && \
    apt-get -y install python && \
    dpkg -i /root/test_app.deb

CMD ["/bin/sh"]

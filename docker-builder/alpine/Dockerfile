FROM alpine

MAINTAINER Albert Monfà

RUN apk update && \
    apk add make py2-pip python-dev py-virtualenv ruby ruby-dev ruby-rdoc \
	ruby-irb gcc musl-dev musl libffi-dev alpine-sdk && \
	gem install fpm

CMD ["/bin/sh"]

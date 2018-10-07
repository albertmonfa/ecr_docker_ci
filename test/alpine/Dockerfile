FROM alpine

MAINTAINER Albert Monfà

COPY test_app.apk /root/test_app.apk

RUN apk update && \
    apk add --allow-untrusted /root/test_app.apk

CMD ["/bin/sh"]

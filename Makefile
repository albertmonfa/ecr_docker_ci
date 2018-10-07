.DEFAULT_GOAL := help

iteration = $(pwd date +'%s')
version = 0.0.1
build_path = build
python_deps = boto3 virtualenv-tools ConfigArgParse docker-py PyYAML jsonschema
pkg_name = ecr-docker-ci
arch = amd64
maintaniner = 'Albert Monfà'
description =  'ECR-docker-ci bulding and pushing docker images to Amazon ECR'
license = 'Apache 2.0'
docker_test_cmd = ecr-docker-ci -h

python-virtual-env:
	mkdir -p $(build_path)/usr/share/python
	virtualenv $(build_path)/usr/share/python/$(pkg_name)
	$(build_path)/usr/share/python/$(pkg_name)/bin/pip install -U pip distribute
	$(build_path)/usr/share/python/$(pkg_name)/bin/pip uninstall -y distribute
	$(build_path)/usr/share/python/$(pkg_name)/bin/pip install $(python_deps)
	find build ! -perm -a+r -exec chmod a+r {} \;
	cd $(build_path)/usr/share/python/$(pkg_name) && \
	sed -i "s/'\/bin\/python'/\('\/bin\/python','\/bin\/python2'\)/g" \
	lib/python2.7/site-packages/virtualenv_tools.py && \
	./bin/virtualenv-tools --update-path /usr/share/python/$(pkg_name)
	find $(build_path) -iname *.pyc -exec rm {} \;
	find $(build_path) -iname *.pyo -exec rm {} \;

source:
	@mkdir -p $(build_path)/usr/sbin/
	@cp -ra src/* $(build_path)/usr/sbin/$(pkg_name)
	@chmod +x $(build_path)/usr/sbin/$(pkg_name)
	@sed -i 's/usr\/bin\/python/usr\/share\/python\/$(pkg_name)\/bin\/python/g' \
	$(build_path)/usr/sbin/$(pkg_name)

builder_deb:
	@fpm \
	--depends python \
	--deb-user root \
	--deb-group root \
	--description $(description) \
	--license $(license) \
	-t deb -s dir -C $(build_path) -n $(pkg_name) -v $(version) -p \
	packages/deb/$(pkg_name)_$(version)_$(iteration)_$(arch).deb \
	-a $(arch) -m $(maintainer)
	@cp -af packages/deb/$(pkg_name)_$(version)_$(iteration)_$(arch).deb \
	test/debian/test_app.deb
	@mv packages/deb/$(pkg_name)_$(version)_$(iteration)_$(arch).deb \
	packages/deb/$(pkg_name)_$(version)_$(arch).deb

builder_rpm:
	@fpm \
	--depends python \
	--rpm-user root \
	--rpm-group root \
	--description $(description) \
	--license $(license) \
	-t rpm -s dir -C $(build_path) -n $(pkg_name) -v $(version) -p \
	packages/rpm/$(pkg_name)_$(version)_$(iteration)_$(arch).rpm \
	-a $(arch)
	@cp -af packages/rpm/$(pkg_name)_$(version)_$(iteration)_$(arch).rpm \
	test/centos/test_app.rpm
	@mv packages/rpm/$(pkg_name)_$(version)_$(iteration)_$(arch).rpm \
	packages/rpm/$(pkg_name)_$(version)_$(arch).rpm

builder_apk:
	@sed -i 's/usr\/share\/python\/$(pkg_name)\/bin\/python/usr\/bin\/python/g' \
	$(build_path)/usr/sbin/$(pkg_name)
	@fpm \
	--depends python2 \
	--depends py2-pip \
	--depends python-dev \
	--post-install scripts/post-install-apk \
	-t apk -s dir -C $(build_path) -n $(pkg_name) -v $(version) -p \
	packages/apk/$(pkg_name)_$(version)_$(iteration)_$(arch).apk \
	-a $(arch) -m $(maintainer)
	@cp -af packages/apk/$(pkg_name)_$(version)_$(iteration)_$(arch).apk \
	test/alpine/test_app.apk
	@mv packages/apk/$(pkg_name)_$(version)_$(iteration)_$(arch).apk \
	packages/apk/$(pkg_name)_$(version)_$(arch).apk

rpm:
	@cd docker-builder/centos/ && docker build -t builder_$(pkg_name)_centos . \
	1> /dev/null
	@docker run -it -v $(shell pwd):/root/ builder_$(pkg_name)_centos \
	/bin/sh -c 'cd /root/ && make docker_rpm' 1> /dev/null

deb:
	@cd docker-builder/debian/ && docker build -t builder_$(pkg_name)_debian . \
	1> /dev/null 1> /dev/null
	@docker run -it -v $(shell pwd):/root/ builder_$(pkg_name)_debian \
	/bin/sh -c 'cd /root/ && make docker_deb' 1> /dev/null

apk:
	@cd docker-builder/alpine/ && docker build -t builder_$(pkg_name)_alpine . \
	1> /dev/null
	@docker run -it -v $(shell pwd):/root/ builder_$(pkg_name)_alpine \
	/bin/sh -c 'cd /root/ && make docker_apk' 1> /dev/null

docker_rpm: | clean_build python-virtual-env source builder_rpm

docker_deb: | clean_build python-virtual-env source builder_deb

docker_apk: | clean_build source builder_apk

test: | test_alpine test_centos test_debian

test_alpine:
	@cd test/alpine/ && docker build -t test_$(pkg_name)_alpine . 1> /dev/null
	docker run -it test_$(pkg_name)_alpine $(docker_test_cmd)

test_debian:
	@cd test/debian/ && docker build -t test_$(pkg_name)_debian . 1> /dev/null
	docker run -it test_$(pkg_name)_debian $(docker_test_cmd)

test_centos:
	@cd test/centos/ && docker build -t test_$(pkg_name)_centos . 1> /dev/null
	docker run -it test_$(pkg_name)_centos $(docker_test_cmd)

clean: | clean_build clean_test

clean_build:
	@rm -rf $(build_path)

clean_test:
	@test -f test/centos/test_app.rpm && rm test/centos/test_app.rpm
	@test -f test/debian/test_app.deb && rm test/debian/test_app.deb
	@test -f test/alpine/test_app.apk && rm test/alpine/test_app.apk

all: | deb rpm apk test clean

help:
	@echo "TARGETS: all rpm deb apk clean test"

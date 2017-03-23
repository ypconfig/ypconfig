PREFIX=$(CURDIR)/debian/

install: ypconfig

ypconfig: PKGNAME	:= ypconfig
ypconfig: PKGPREFIX	:= $(PREFIX)/$(PKGNAME)
ypconfig: SDIR		:= ypconfig

ypconfig:
	python setup.py install --force --root=$(PKGPREFIX) --no-compile -O0 --install-layout=deb
	mkdir -p $(PKGPREFIX)/etc/ypconfig/
	mkdir -p $(PKGPREFIX)/usr/sbin/
	mkdir -p $(PKGPREFIX)/usr/lib/ypconfig/
	install -m 750 ./ypconfig $(PKGPREFIX)/usr/sbin/
	install -m 755 ./playground/snmp-helper.py $(PKGPREFIX)/usr/lib/ypconfig

clean:
	rm -rf $(PREFIX)/ypconfig

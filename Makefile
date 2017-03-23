PREFIX=$(CURDIR)/debian
PKGNAME=ypconfig
PKGPREFIX=$(PREFIX)/$(PKGNAME)
SDIR=ypconfig

install:
	python setup.py install --force --root=$(PKGPREFIX) --no-compile -O0 --install-layout=deb
	mkdir -p $(PKGPREFIX)/etc/ypconfig/
	mkdir -p $(PKGPREFIX)/usr/sbin/
	mkdir -p $(PKGPREFIX)/usr/lib/ypconfig/
	install -m 750 ypconfig $(PKGPREFIX)/usr/sbin/
	install -m 755 playground/snmp-helper.py $(PKGPREFIX)/usr/lib/ypconfig
	install -m 644 requirements.txt $(PKGPREFIX)/etc/ypconfig/

clean:
	rm -rf $(PREFIX)/ypconfig

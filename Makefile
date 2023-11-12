PREFIX=$(CURDIR)/debian
PKGNAME=ypconfig
PKGPREFIX=$(PREFIX)/$(PKGNAME)
SDIR=ypconfig

install:
	python3 setup.py install --force --root=/ --no-compile -O0 --install-scripts=$(PKGPREFIX)/usr/sbin --prefix=$(PKGPREFIX)/usr
	mkdir -p $(PKGPREFIX)/etc/ypconfig/
	mkdir -p $(PKGPREFIX)/usr/sbin/
	mkdir -p $(PKGPREFIX)/usr/lib/ypconfig/
	install -m 755 playground/snmp-helper.py $(PKGPREFIX)/usr/lib/ypconfig
	install -m 644 requirements.txt $(PKGPREFIX)/etc/ypconfig/

clean:
	rm -rf $(PREFIX)/ypconfig

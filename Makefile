DESTDIR ?= /usr/local/bin

.PHONY: install

install:
	ln -srv g3.py $(DESTDIR)/g3

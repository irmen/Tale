.PHONY: zips clean all

all:
	@echo "targets are: zips clean"

zips: clean
	echo "Making zips"
	python -m tale.author zip circle circle.pyz
	python -m tale.author zip demo demo.pyz
	python -m tale.author zip zed_is_me zed_is_me.pyz

clean:
	echo "cleaning"
	find . -name *.pyc -or -name *.pyo -or -name __pycache__ | xargs rm -rf
	rm -f *.zip *.pyz


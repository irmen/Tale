.PHONY: zips clean all

all:
	@echo "targets are: zips clean"

zips: clean
	echo "Making zips"
	7z a circle.zip ./circle/*
	7z a demo.zip ./demo/*
	7z a zed.zip ./zed_is_me/*


clean:
	echo "cleaning"
	find . -name *.pyc -or -name *.pyo -or -name __pycache__ | xargs rm -rf
	rm -f *.zip

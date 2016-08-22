.DEFAULT_GOAL := all
.PHONY: all
all:
	if ! [ -f .env/bin/activate ]; then virtualenv2 .env; else echo "Virtual env already exists, skipping."; fi
	.env/bin/pip2 install -r requirements.txt
	sudo .env/bin/python2 ./app.py

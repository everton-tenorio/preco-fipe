#!/bin/sh

cd app
pip install --upgrade pip
pip install -r requirements.txt
python app.py

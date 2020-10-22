#!/bin/bash
cd $1
rm -rf dist
mkdir dist
cd dist
virtualenv env
source env/bin/activate
pip install -r /build/requirements.txt
mkdir package
cp -r env/lib/python3.8/site-packages/* package
cp -r /flask-serverless/flask_serverless package
cp ../production.py package
cp /rediner/demo/view.py package
cp -r /rediner/demo/templates package
cp -r /rediner/demo/assets package
find package -name __pycache__ -exec rm -rf {} \;
rm -f ../lambda.zip
cd package
zip -r ../../lambda.zip .

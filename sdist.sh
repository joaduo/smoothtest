#!/bin/bash
pandoc --from=markdown --to=rst --output=README README.md

app="smoothtest"

rm dist/$app\-*.tar.gz

python setup.py sdist && python setup.py check -r

if [ "$1" == "venv" ] ;  then
	#test installation
	mkdir venv -p
	cd venv
	virtualenv ./
	source bin/activate
	pip install ../dist/$app\-*.tar.gz
	pip uninstall $app -y
	cd ..
	#rm venv -Rf
fi

echo 
echo "upload with: python setup.py sdist upload -r pypi"

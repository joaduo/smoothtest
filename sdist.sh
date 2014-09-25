#!/bin/bash
pandoc --from=markdown --to=rst --output=README README.md

#python smoothtest/smoke/SmokeTestDiscover.py -p smoothtest/

python -m unittest discover && python setup.py sdist && python setup.py check -r

echo 
echo "upload with: python setup.py sdist upload -r pypi"

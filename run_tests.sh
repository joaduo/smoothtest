#!/bin/bash

pushd `dirname $0` > /dev/null
    pip install -r test_requirements.txt
    python -m smoothtest.discover.SmokeTestDiscover -P smoothtest
popd > /dev/null

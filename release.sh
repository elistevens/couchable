#!/bin/bash

VER=$1
UPLOAD=$2

if [ "$VER" == "" ]
then
    echo "Must specify a version number."
    echo "./release.sh 9.9.9a1 upload"
    git tag | tail -n 10
    exit
fi

if git diff --quiet HEAD || true
then

    python setup.py nosetests \
    && sed -i'' -e "s/version='.*'/version='$VER'/" setup.py \
    && git commit -am "v$VER" \
    && python setup.py bdist_egg sdist $UPLOAD \
    && git push origin \
    && git tag $VER \
    && git push --tags origin

else
    echo Uncommitted changes.
    git status
fi

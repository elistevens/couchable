#!/bin/bash

VER=$1
UPLOAD=$2

if [ "$VER" == "" ]
then
    echo "Must specify a version number."
    exit
fi

if git diff --quiet HEAD
then

    git tag $VER \
    && sed -i '' -e "s/version='.*'/version='$VER'/" setup.py \
    && python setup.py nosetests \
    && python setup.py bdist_egg $UPLOAD \
    && git commit -am "v$VER" \
    && git push github \
    && git push --tags github

else
    echo Uncommitted changes.
    git status
fi

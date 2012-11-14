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

if git diff --quiet HEAD
then

    python setup.py nosetests \
    && git tag $VER \
    && sed -i '' -e "s/version='.*'/version='$VER'/" setup.py \
    && python setup.py bdist_egg sdist $UPLOAD \
    && git commit -am "v$VER" \
    && git push github \
    && git push --tags github

else
    echo Uncommitted changes.
    git status
fi

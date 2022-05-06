#!/bin/bash

URL=$1
PROJECT=$2
DOMAIN=$3
# clone project to home assistant config dir
git clone ${URL} --depth=1
# remove exist files
rm -rf custom_components/${DOMAIN}
# copy folder to custom_components dir
cp -r ./${PROJECT}/custom_components/${DOMAIN} custom_components/${DOMAIN}
# remove files
rm -rf ${PROJECT}
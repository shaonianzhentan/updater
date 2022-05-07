#!/bin/bash

# get current dir
project_path=$(cd `dirname $0`; pwd)

BRANCH=$1
URL=$2
PROJECT=$3
DOMAIN=$4
# clone project to home assistant config dir
git clone -b ${BRANCH} ${URL} --depth=1
# remove exist files
rm -rf custom_components/${DOMAIN}
# copy folder to custom_components dir
cp -r ./${PROJECT}/custom_components/${DOMAIN} custom_components/${DOMAIN}
# remove files
rm -rf ${PROJECT}

# remove tmp sh files
rm -rf ${project_path}/${DOMAIN}.sh
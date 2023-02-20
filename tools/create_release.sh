#!/bin/bash
#Tar command to create a release, excluding unuseful folders and files.

BASEDIR=$(dirname "$0")
cd ${BASEDIR}/../..

BUNDLED=${1}
if [[ ${BUNDLED} == '--bundled' ]]
then
    ARCHIVE_NAME='rtkbase.tar.xz'
    TAR_ARG='-cJf'
else
    ARCHIVE_NAME='rtkbase.tar.gz'
    TAR_ARG='-zcvf'
fi

tar --exclude-vcs \
    --exclude='rtkbase/data' \
    --exclude='rtkbase/drawing' \
    --exclude='rtkbase/images' \
    --exclude='rtkbase/log' \
    --exclude='rtkbase/logs' \
    --exclude='rtkbase/.vscode' \
    --exclude='rtkbase/.github' \
    --exclude='rtkbase/settings.conf' \
    --exclude='test.sh' \
    --exclude='test.conf' \
    --exclude='*.pyc' \
    $TAR_ARG $ARCHIVE_NAME rtkbase/
 
echo '========================================================'
echo 'Archive ' $ARCHIVE_NAME ' created inside' $(pwd)
echo '========================================================'

if [[ ${BUNDLED} == '--bundled' ]]
then
    cat rtkbase/tools/install.sh $ARCHIVE_NAME > install.sh
    chmod +x install.sh
    echo 'Bundled script install.sh created inside' $(pwd)
    echo '========================================================'

fi
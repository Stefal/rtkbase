#!/bin/bash
#Tar command to create a release, excluding unuseful folders and files.

BASEDIR=$(dirname "$0")
cd ${BASEDIR}/../..
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
    -zcvf rtkbase.tar.gz rtkbase/
echo '========================================================'
echo 'Archive rtkbase.tar.gz created inside' $(pwd)
echo '========================================================'
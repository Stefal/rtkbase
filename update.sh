#!/bin/bash -x

sleep 1

git fetch

if [[ $? -eq 0 ]];
then
    echo "Successfully updated remote repo info, resetting to master..."
    git reset --hard origin/master

    echo "Copying default configs to RTKLIB directory"
    cp /home/ReachView/rtklib_configs/* /home/RTKLIB/app/rtkrcv/
fi

/home/reach/ReachView/server.py

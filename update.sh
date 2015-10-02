#!/bin/bash -x

sleep 1

git fetch

if [[ $? -eq 0 ]];
then
    echo "Successfully updated remote repo info, resetting to master..."
    git checkout master
    git reset --hard origin/master

    echo "Copying default configs to RTKLIB directory"
    cp /home/ReachView/rtklib_configs/*.conf /home/RTKLIB/app/rtkrcv/

    cp /home/ReachView/rtklib_configs/rtkrcv /home/RTKLIB/app/rtkrcv/gcc/
    cp /home/ReachView/rtklib_configs/str2str /home/RTKLIB/app/str2str/gcc/
fi

/home/reach/ReachView/server.py
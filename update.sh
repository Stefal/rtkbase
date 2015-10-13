#!/bin/bash -x

sleep 1

git fetch

if [[ $? -eq 0 ]];
then
    echo "Successfully updated remote repo info, resetting to master..."
    git checkout master
    git reset --hard origin/master

    echo "Copying default configs to RTKLIB directory"
    cp /home/reach/ReachView/rtklib_configs/*.conf /home/reach/RTKLIB/app/rtkrcv/
    cp /home/reach/ReachView/rtklib_configs/*.cmd /home/reach/RTKLIB/app/rtkrcv/

    cp /home/reach/ReachView/rtklib_configs/rtkrcv /home/reach/RTKLIB/app/rtkrcv/gcc/
    cp /home/reach/ReachView/rtklib_configs/str2str /home/reach/RTKLIB/app/str2str/gcc/
fi

chown -R reach:users /home/reach
/home/reach/ReachView/server.py

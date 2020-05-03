#!/bin/bash

### RTKBASE INSTALLATION SCRIPT ###

install_dependency() {
    apt-get update 
    apt-get install -y git build-essential python3-pip python3-dev python3-setuptools python3-wheel libsystemd-dev bc dos2unix 
}

install_rtklib() {
    #Get Rtklib 2.4.3 repository
    sudo -u $(logname) git clone -b rtklib_2.4.3 --single-branch https://github.com/tomojitakasu/RTKLIB
    #Install Rtklib app
    #TODO add correct CTARGET in makefile?
    make --directory=RTKLIB/app/str2str/gcc
    make --directory=RTKLIB/app/str2str/gcc install
    make --directory=RTKLIB/app/rtkrcv/gcc
    make --directory=RTKLIB/app/rtkrcv/gcc install
    make --directory=RTKLIB/app/convbin/gcc
    make --directory=RTKLIB/app/convbin/gcc install
    #deleting RTKLIB
    rm -rf RTKLIB/
}

install_rtkbase() {
    if [ "$1" == "--from-repo" ]
    then
        #Get rtkbase repository
        sudo -u $(logname) git clone -b web_gui --single-branch https://github.com/stefal/rtkbase.git
    elif [ "$1" == "--release" ]
    then
        #Get rtkbase latest release
        sudo -u $(logname) wget https://github.com/stefal/rtkbase/releases/latest/download/rtkbase.tar.gz
        sudo -u $(logname) tar -xvf rtkbase.tar.gz
    fi

    #as we need to run the web server as root, we need to install the requirements with
    #the same user
    python3 -m pip install --upgrade pip setuptools wheel  --extra-index-url https://www.piwheels.org/simple
    python3 -m pip install -r rtkbase/web_app/requirements.txt  --extra-index-url https://www.piwheels.org/simple
    #when we will be able to launch the web server without root, we will use
    #sudo -u $(logname) python3 -m pip install -r requirements.txt --user
    #Install unit files
    rtkbase/copy_unit.sh
    systemctl enable rtkbase_web.service
    systemctl daemon-reload
    #systemctl enable rtkbase_web.service
    #systemctl enable rtkbase_web.service
}

main() {
    if [ "$1" == "--release" ] || [ "$1" == "--from-repo" ]
    then
        install_dependency
        install_rtklib
        install_rtkbase $1
    else
        echo "Wrong parameter: Please use --release or --from-repo"
    fi
}

main $1
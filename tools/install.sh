#!/bin/bash

### RTKBASE INSTALLATION SCRIPT ###

declare -a detected_gnss

install_dependencies() {
    echo '################################'
    echo 'INSTALLING DEPENDENCIES'
    echo '################################'
    apt-get update 
    apt-get install -y git build-essential python3-pip python3-dev python3-setuptools python3-wheel libsystemd-dev bc dos2unix 
}

install_rtklib() {
    echo '################################'
    echo 'INSTALLING RTKLIB'
    echo '################################'
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
    echo '################################'
    echo 'INSTALLING RTKBASE'
    echo '################################'
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
    systemctl start rtkbase_web.service
}

detect_usb_gnss() {
    echo '################################'
    echo 'GNSS RECEIVER DETECTION'
    echo '################################'
    #This function put the (USB) detected gnss receiver informations in detected_gnss
    #If there are several receiver, only the last one will be present in the variable
    for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do

        syspath="${sysdevpath%/dev}"
        devname="$(udevadm info -q name -p $syspath)"
        if [[ "$devname" == "bus/"* ]]; then continue; fi
        eval "$(udevadm info -q property --export -p $syspath)"
        if [[ -z "$ID_SERIAL" ]]; then continue; fi
        if [[ "$ID_SERIAL" =~ ^(U-blox|skytraq)$ ]]; then continue; fi
        detected_gnss[0]=$devname
        detected_gnss[1]=$ID_SERIAL
    done

}

main() {
    if [ "$1" == "--release" ] || [ "$1" == "--from-repo" ]
    then
        install_dependencies
        install_rtklib
        install_rtkbase $1
        #if a gnss receiver is detected, write the com port in settings.conf
        detect_usb_gnss
        if [[ ${#detected_gnss[*]} -eq 2 ]]
        then
            echo 'GNSS RECEIVER DETECTED: /dev/'${detected_gnss[0]} ' - ' ${detected_gnss[1]}
            if [[ -f "rtkbase/settings.conf"]]  #check if settings.conf exists
            then
                #inject the com port inside settings.conf
                sudo -u $(logname) sed -i s/com_port=.*/com_port=\'${detected_gnss[0]}\'/ ${destination_directory}/settings.conf
            else
                #create settings.conf with only the com_port setting
                printf "[main]\ncom_port='"${detected_gnss[0]}"'\n" > rtkbase/settings.conf
            fi
        fi

    else
        echo "Wrong parameter: Please use --release or --from-repo"
    fi
}

main $1
#!/bin/bash

### RTKBASE INSTALLATION SCRIPT ###
declare -a detected_gnss

man_help(){
    echo '################################'
    echo 'RTKBASE INSTALLATION HELP'
    echo '################################'
    echo 'Bash scripts for install a simple gnss base station with a web frontend.'
    echo ''
    echo ''
    echo ''
    echo '* Before install, connect your gnss receiver to raspberry pi/orange pi/.... with usb or uart.'
    echo '* Running install script with sudo'
    echo ''
    echo '        sudo ./install.sh'
    echo ''
    echo 'Options:'
    echo '        --all'
    echo '                         Install all dependencies, Rtklib, last release of Rtkbase, services,'
    echo '                         crontab jobs, detect your GNSS receiver and configure it.'
    echo ''
    echo '        --dependencies'
    echo '                         Install all dependencies like git build-essential python3-pip ...'
    echo ''
    echo '        --rtklib'
    echo '                         Clone RTKlib 2.4.3 from github and compile it.'
    echo '                         https://github.com/tomojitakasu/RTKLIB/tree/rtklib_2.4.3'
    echo ''
    echo '        --rtkbase-release'
    echo '                         Get last release of RTKBASE:'
    echo '                         https://github.com/Stefal/rtkbase/releases'
    echo ''
    echo '        --rtkbase-repo'
    echo '                         Clone RTKBASE from github:'
    echo '                         https://github.com/Stefal/rtkbase/tree/web_gui'
    echo ''
    echo '        --unit-files'
    echo '                         Deploy services.'
    echo ''
    echo '        --crontab'
    echo '                         add crontab tools, every day logs are store'
    echo ''
    echo ''
    echo '        --detect-usb-gnss'
    echo '                         Detect your GNSS receiver.'
    echo ''
    echo ''
    echo '        --configure-gnss'
    echo '                         Configure your GNSS receiver.'
    echo ''
    echo
    exit 0
}

install_dependencies() {
    echo '################################'
    echo 'INSTALLING DEPENDENCIES'
    echo '################################'
      apt-get update 
      apt-get install -y git build-essential python3-pip python3-dev python3-setuptools python3-wheel libsystemd-dev bc dos2unix socat
}

install_rtklib() {
    echo '################################'
    echo 'INSTALLING RTKLIB'
    echo '################################'
      # str2str already exist?
      if [ ! -f /usr/local/bin/str2str ]
      then 
        rm -rf RTKLIB/
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
      else
        echo 'str2str already exist'
      fi
}

rtkbase_repo(){
    #Get rtkbase repository
    sudo -u $(logname) git clone -b web_gui --single-branch https://github.com/stefal/rtkbase.git
    sudo -u $(logname) sed -i s/user=.*/^user=$(logname)/ rtkbase/settings.conf

}

rtkbase_release(){
    #Get rtkbase latest release
    sudo -u $(logname) wget https://github.com/stefal/rtkbase/releases/latest/download/rtkbase.tar.gz -O rtkbase.tar.gz
    sudo -u $(logname) tar -xvf rtkbase.tar.gz
    sudo -u $(logname) sed -i s/user=.*/^user=$(logname)/ rtkbase/settings.conf

}

install_rtkbase_from_repo() {
    echo '################################'
    echo 'INSTALLING RTKBASE FROM REPO'
    echo '################################'
      if [ -d rtkbase ]
      then
        if [ -d rtkbase/.git ]
        then
          echo "RtkBase repo: YES, git pull"
          git -C rtkbase pull
        else
          echo "RtkBase repo: NO, rm release & git clone rtkbase"
          rm -r rtkbase
          rtkbase_repo
        fi
      else
        echo "RtkBase repo: NO, git clone rtkbase"
        rtkbase_repo
      fi
}

install_rtkbase_from_release() {
    echo '################################'
    echo 'INSTALLING RTKBASE FROM RELEASE'
    echo '################################'
      if [ -d rtkbase ]
      then
        if [ -d rtkbase/.git ]
        then
          echo "RtkBase release: NO, rm repo & download last release"
          rm -r rtkbase
          rtkbase_release
        else
          echo "RtkBase release: YES, rm & deploy last release"
          rtkbase_release
        fi
      else
        echo "RtkBase release: NO, download & deploy last release"
        rtkbase_release
      fi
}

rtkbase_requirements(){
    echo '################################'
    echo 'INSTALLING RTKBASE REQUIREMENTS'
    echo '################################'
      #as we need to run the web server as root, we need to install the requirements with
      #the same user
      python3 -m pip install --upgrade pip setuptools wheel  --extra-index-url https://www.piwheels.org/simple
      python3 -m pip install -r rtkbase/web_app/requirements.txt  --extra-index-url https://www.piwheels.org/simple
      # We were waiting for the next pystemd official release.
      # install pystemd dev wheel for arm platform
      python3 -m pip install rtkbase/tools/pystemd-0.8.1590398158-cp37-cp37m-linux_armv7l.whl
      #when we will be able to launch the web server without root, we will use
      #sudo -u $(logname) python3 -m pip install -r requirements.txt --user.
}

install_unit_files() {
    echo '################################'
    echo 'ADDING UNIT FILES'
    echo '################################'
      if [ -d rtkbase ]
      then 
        #Install unit files
        rtkbase/copy_unit.sh
        systemctl enable rtkbase_web.service
        systemctl daemon-reload
        systemctl start rtkbase_web.service
      else
        echo 'RtkBase not installed, use option --rtkbase-release'
      fi
}

add_crontab() {
    echo '################################'
    echo 'ADDING CRONTAB'
    echo '################################'
      if [ -d rtkbase ]
      then 
        #script from https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
        #I've added '-r' to sort because SHELL=/bin/bash should stay before "0 4 * * ..."
        (crontab -u $(logname) -l ; echo 'SHELL=/bin/bash') | sort -r | uniq - | crontab -u $(logname) -
        (crontab -u $(logname) -l ; echo "0 4 * * * $(eval echo ~$(logname)/rtkbase/archive_and_clean.sh)") | sort -r | uniq - | crontab -u $(logname) -
      else
        echo 'RtkBase not installed, use option --rtkbase-release'
      fi
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
          if [[ "$ID_SERIAL" =~ (u-blox|skytraq) ]]
          then
            detected_gnss[0]=$devname
            detected_gnss[1]=$ID_SERIAL
            echo '/dev/'${detected_gnss[0]} ' - ' ${detected_gnss[1]}
          fi
      done
}

configure_gnss(){
    echo '################################'
    echo 'CONFIGURE GNSS RECEIVER'
    echo '################################'
      if [ -d rtkbase ]
      then 
        if [[ ${#detected_gnss[*]} -eq 2 ]]
        then
          echo 'GNSS RECEIVER DETECTED: /dev/'${detected_gnss[0]} ' - ' ${detected_gnss[1]}
          if [[ -f "rtkbase/settings.conf" ]]  #check if settings.conf exists
          then
            #inject the com port inside settings.conf
            sudo -u $(logname) sed -i s/^com_port=.*/com_port=\'${detected_gnss[0]}\'/ rtkbase/settings.conf
          else
            #create settings.conf with the com_port setting and the format
            sudo -u $(logname) printf "[main]\ncom_port='"${detected_gnss[0]}"'\ncom_port_settings='115200:8:n:1'" > rtkbase/settings.conf
          fi
        fi
        #if the receiver is a U-Blox, launch the set_zed-f9p.sh. This script will reset the F9P and configure it with the corrects settings for rtkbase
        if [[ ${detected_gnss[1]} =~ 'u-blox' ]]
        then
          rtkbase/tools/set_zed-f9p.sh /dev/${detected_gnss[0]} 115200 rtkbase/receiver_cfg/U-Blox_ZED-F9P_rtkbase.txt
        fi
      else
        echo 'RtkBase not installed, use option --rtkbase-release'
      fi
}

main() {
  #display parameters
  echo 'Installation options: ' $@
  array=($@)
  # if no parameters display help
  if [ -z "$array" ]                  ; then man_help                        ;fi
  # run intall options
  for i in "${array[@]}"
  do
    if [ "$1" == "--help" ]           ; then man_help                        ;fi
    if [ "$i" == "--dependencies" ]   ; then install_dependencies            ;fi
    if [ "$i" == "--rtklib" ] 	      ; then install_rtklib                  ;fi
    if [ "$i" == "--rtkbase-release" ]; then install_rtkbase_from_release && \
					     rtkbase_requirements            ;fi
    if [ "$i" == "--rtkbase-repo" ]   ; then install_rtkbase_from_repo    && \
					     rtkbase_requirements            ;fi
    if [ "$i" == "--unit-files" ]     ; then install_unit_files              ;fi
    if [ "$i" == "--crontab" ] 	      ; then add_crontab                     ;fi
    if [ "$i" == "--detect-usb-gnss" ]; then detect_usb_gnss                 ;fi
    if [ "$i" == "--configure-gnss" ]     ; then configure_gnss                      ;fi
    if [ "$i" == "--all" ]            ; then install_dependencies         && \
					     install_rtklib               && \
					     install_rtkbase_from_release && \
					     rtkbase_requirements         && \
					     install_unit_files           && \
					     add_crontab                  && \
					     detect_usb_gnss              && \
					     configure_gnss                   && \
					     systemctl start str2str_tcp     ;fi

  done
  echo '################################'
  echo 'END OF INSTALLATION'
  echo 'Open your browser to http://'$(hostname -I)
  echo '################################'
}

main $@
exit 0

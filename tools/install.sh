#!/bin/bash

### RTKBASE INSTALLATION SCRIPT ###
declare -a detected_gnss

man_help(){
    echo '################################'
    echo 'RTKBASE INSTALLATION HELP'
    echo '################################'
    echo 'Bash scripts to install a simple gnss base station with a web frontend.'
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
    echo '        --gpsd-chrony'
    echo '                         Install gpsd and chrony to set date and time'
    echo '                         from the gnss receiver.'
    echo ''
    echo '        --detect-usb-gnss'
    echo '                         Detect your GNSS receiver.'
    echo ''
    echo '        --configure-gnss'
    echo '                         Configure your GNSS receiver.'
    echo ''
    echo '        --start-services'
    echo '                         Start services (rtkbase_web, str2str_tcp, gpsd, chrony)'
    exit 0
}

install_dependencies() {
    echo '################################'
    echo 'INSTALLING DEPENDENCIES'
    echo '################################'
      apt-get update 
      apt-get install -y git build-essential pps-tools python3-pip python3-dev python3-setuptools python3-wheel libsystemd-dev bc dos2unix socat zip unzip
}

install_gpsd_chrony() {
    echo '################################'
    echo 'CONFIGURING FOR USING GPSD + CHRONY'
    echo '################################'
      apt-get install chrony
      #Disabling and masking systemd-timesyncd
      systemctl stop systemd-timesyncd
      systemctl disable systemd-timesyncd
      systemctl mask systemd-timesyncd
      #Adding GPS as source for chrony
      grep -q 'set larger delay to allow the GPS' /etc/chrony/chrony.conf || echo '# set larger delay to allow the GPS source to overlap with the other sources and avoid the falseticker status
' >> /etc/chrony/chrony.conf
      grep -qxF 'refclock SHM 0 refid GPS precision 1e-1 offset 0 delay 0.2' /etc/chrony/chrony.conf || echo 'refclock SHM 0 refid GPS precision 1e-1 offset 0 delay 0.2' >> /etc/chrony/chrony.conf
      #Adding PPS as an optionnal source for chrony
      grep -q 'refclock PPS /dev/pps0 refid PPS lock GPS' /etc/chrony/chrony.conf || echo '#refclock PPS /dev/pps0 refid PPS lock GPS' >> /etc/chrony/chrony.conf

      #Overriding chrony.service with custom dependency
      cp /lib/systemd/system/chrony.service /etc/systemd/system/chrony.service
      sed -i s/^After=.*/After=gpsd.service/ /etc/systemd/system/chrony.service

      #If needed, adding backports repository to install a gpsd release that support the F9P
      if lsb_release -c | grep -qE 'bionic|buster'
      then
        if ! apt-cache policy | grep -qE 'buster-backports.* armhf'
        then
          #Adding buster-backports
          echo 'deb http://httpredir.debian.org/debian buster-backports main contrib' > /etc/apt/sources.list.d/backports.list
          apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 648ACFD622F3D138
          apt-get update
        fi
        apt-get -t buster-backports install gpsd -y
      else
        #We hope that the release is more recent than buster and provide gpsd 3.20 or >
        apt-get install gpsd -y
      fi
      #disable hotplug
      sed -i 's/^USBAUTO=.*/USBAUTO="false"/' /etc/default/gpsd
      #Setting correct input for gpsd
      sed -i 's/^DEVICES=.*/DEVICES="tcp:\/\/127.0.0.1:5015"/' /etc/default/gpsd
      #Adding example for using pps
      sed -i '/^DEVICES=.*/a #DEVICES="tcp:\/\/127.0.0.1:5015 \/dev\/pps0"' /etc/default/gpsd
      #gpsd should always run, in read only mode
      sed -i 's/^GPSD_OPTIONS=.*/GPSD_OPTIONS="-n -b"/' /etc/default/gpsd
      #Overriding gpsd.service with custom dependency
      cp /lib/systemd/system/gpsd.service /etc/systemd/system/gpsd.service
      sed -i 's/^After=.*/After=str2str_tcp.service/' /etc/systemd/system/gpsd.service
      if grep -qxF '^BindsTo=' /etc/systemd/system/gpsd.service
      then
        #Change the BindsTo value
        sed -i 's/^BindsTo=.*/BindsTo=str2str_tcp.service/' /etc/systemd/system/gpsd.service
      else
        #Add the BindsTo value
        sed -i '/^After=.*/i BindsTo=str2str_tcp.service' /etc/systemd/system/gpsd.service
      fi

      #Reload systemd services and enable chrony and gpsd
      systemctl daemon-reload
      systemctl enable gpsd
      systemctl enable chrony
      #Enable chrony can fail but it works, so let's return 0 to not break the script.
      return 0
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
    sudo -u $(logname) git clone https://github.com/stefal/rtkbase.git
    sudo -u $(logname) touch rtkbase/settings.conf

}

rtkbase_release(){
    #Get rtkbase latest release
    sudo -u $(logname) wget https://github.com/stefal/rtkbase/releases/latest/download/rtkbase.tar.gz -O rtkbase.tar.gz
    sudo -u $(logname) tar -xvf rtkbase.tar.gz
    sudo -u $(logname) touch rtkbase/settings.conf

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
        systemctl enable rtkbase_archive.timer
        systemctl daemon-reload
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
          if [[ ${detected_gnss[1]} =~ 'u-blox' ]]
          then
            gnss_format='ubx'
          fi
          if [[ -f "rtkbase/settings.conf" ]]  && grep -E "^com_port=.*" rtkbase/settings.conf #check if settings.conf exists
          then
            #change the com port value inside settings.conf
            sudo -u $(logname) sed -i s/^com_port=.*/com_port=\'${detected_gnss[0]}\'/ rtkbase/settings.conf
          else
            #create settings.conf with the com_port setting and the settings needed to start str2str_tcp
            #as it could start before the web server merge settings.conf.default and settings.conf
            sudo -u $(logname) printf "[main]\ncom_port='"${detected_gnss[0]}"'\ncom_port_settings='115200:8:n:1'\nreceiver_format='"${gnss_format}"'\ntcp_port='5015'\n" > rtkbase/settings.conf
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

start_services() {
  echo '################################'
  echo 'STARTING SERVICES'
  echo '################################'
  systemctl daemon-reload
  systemctl start rtkbase_web.service
  systemctl start str2str_tcp.service
  systemctl restart gpsd.service
  systemctl restart chrony.service
  systemctl start rtkbase_archive.timer
  echo '################################'
  echo 'END OF INSTALLATION'
  echo 'You can open your browser to http://'$(hostname -I)
  echo '################################'
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
    if [ "$i" == "--gpsd-chrony" ]    ; then install_gpsd_chrony             ;fi
    if [ "$i" == "--detect-usb-gnss" ]; then detect_usb_gnss                 ;fi
    if [ "$i" == "--configure-gnss" ] ; then configure_gnss                  ;fi
    if [ "$i" == "--start-services" ] ; then start_services                  ;fi
    if [ "$i" == "--all" ]            ; then install_dependencies         && \
					     install_rtklib               && \
					     install_rtkbase_from_release && \
					     rtkbase_requirements         && \
					     install_unit_files           && \
					     install_gpsd_chrony          && \
					     detect_usb_gnss              && \
					     configure_gnss               && \
               start_services               ;fi
  done
}

main $@
exit 0

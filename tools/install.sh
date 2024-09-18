#!/bin/bash

### RTKBASE INSTALLATION SCRIPT ###
declare -a detected_gnss
declare RTKBASE_USER
APT_TIMEOUT='-o dpkg::lock::timeout=3000' #Timeout on lock file (Could not get lock /var/lib/dpkg/lock-frontend)
MODEM_AT_PORT=/dev/ttymodemAT

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
    echo 'Easy installation: sudo ./install.sh --all release'
    echo ''
    echo 'Options:'
    echo '        -a | --all <rtkbase source>'
    echo '                         Install all you need to run RTKBase : dependencies, RTKlib, last release of Rtkbase, services,'
    echo '                         crontab jobs, detect your GNSS receiver and configure it.'
    echo '                         <rtkbase source> could be:'
    echo '                             release  (get the latest available release)'
    echo '                             repo     (you need to add the --rtkbase-repo argument with a branch name)'
    echo '                             url      (you need to add the --rtkbase-custom-source argument with an url)'
    echo '                             bundled  (available if the rtkbase archive is bundled with the install script)'
    echo ''
    echo '        -u | --user'
    echo '                         Use this username as User= inside service unit and for path to rtkbase:'
    echo '                         --user=john will install rtkbase in /home/john/rtkbase'
    echo ''
    echo '        -d | --dependencies'
    echo '                         Install all dependencies like git build-essential python3-pip ...'
    echo ''
    echo '        -r | --rtklib'
    echo '                         Get RTKlib 2.4.3b34j from github and compile it.'
    echo '                         https://github.com/rtklibexplorer/RTKLIB/tree/b34j'
    echo ''
    echo '        -b | --rtkbase-release'
    echo '                         Get last release of RTKBase:'
    echo '                         https://github.com/Stefal/rtkbase/releases'
    echo ''
    echo '        -i | --rtkbase-repo <branch>'
    echo '                         Clone RTKBASE from github with the <branch> parameter used to select the branch.'
    echo ''
    echo '        -j | --rtkbase-bundled'
    echo '                         Extract the rtkbase files bundled with this script, if available.'
    echo ''
    echo '        -f | --rtkbase-custom <source>'
    echo '                         Get RTKBASE from an url.'
    echo ''
    echo '        -t | --unit-files'
    echo '                         Deploy services.'
    echo ''
    echo '        -g | --gpsd-chrony'
    echo '                         Install gpsd and chrony to set date and time'
    echo '                         from the gnss receiver.'
    echo ''
    echo '        -e | --detect-gnss'
    echo '                         Detect your GNSS receiver. It works only with receiver like ZED-F9P.'
    echo ''
    echo '        -n | --no-write-port'
    echo '                         Doesn'\''t write the detected port inside settings.conf.'
    echo '                         Only relevant with --detect-gnss argument.'
    echo ''
    echo '        -c | --configure-gnss'
    echo '                         Configure your GNSS receiver.'
    echo ''
    echo '        -m | --detect-modem'
    echo '                         Detect LTE/4G usb modem'
    echo ''
    echo '        -s | --start-services'
    echo '                         Start services (rtkbase_web, str2str_tcp, gpsd, chrony)'
    echo ''
    echo '        -h | --help'
    echo '                          Display this help message.'

    exit 0
}

_check_user() {
  # RTKBASE_USER is a global variable
  if [ "${1}" != 0 ] ; then
    RTKBASE_USER="${1}"
      #TODO check if user exists and/or path exists ?
      # warning for image creation, do the path exist ?
  elif [[ -z $(logname) ]] ; then
    echo 'The logname command return an empty value. Please reboot and retry.'
    exit 1
  elif [[ $(logname) == 'root' ]]; then
    echo 'The logname command return "root". Please reboot or use --user argument to choose the correct user which should run rtkbase services'
    exit 1
  else
    RTKBASE_USER=$(logname)
  fi
}

install_dependencies() {
    echo '################################'
    echo 'INSTALLING DEPENDENCIES'
    echo '################################'
      apt-get "${APT_TIMEOUT}" update -y || exit 1
      apt-get "${APT_TIMEOUT}" install -y git build-essential pps-tools python3-pip python3-venv python3-dev python3-setuptools python3-wheel python3-serial libsystemd-dev bc dos2unix socat zip unzip pkg-config psmisc proj-bin nftables || exit 1
      apt-get install -y libxml2-dev libxslt-dev || exit 1 # needed for lxml (for pystemd)
      #apt-get "${APT_TIMEOUT}" upgrade -y
}

install_gpsd_chrony() {
    echo '################################'
    echo 'CONFIGURING FOR USING GPSD + CHRONY'
    echo '################################'
      apt-get "${APT_TIMEOUT}" install chrony gpsd -y || exit 1
      #Disabling and masking systemd-timesyncd
      systemctl stop systemd-timesyncd
      systemctl disable systemd-timesyncd
      systemctl mask systemd-timesyncd
      #Adding GPS as source for chrony
      grep -q 'set larger delay to allow the GPS' /etc/chrony/chrony.conf || echo '# set larger delay to allow the GPS source to overlap with the other sources and avoid the falseticker status
' >> /etc/chrony/chrony.conf
      grep -qxF 'refclock SHM 0 refid GNSS precision 1e-1 offset 0 delay 0.2' /etc/chrony/chrony.conf || echo 'refclock SHM 0 refid GNSS precision 1e-1 offset 0 delay 0.2' >> /etc/chrony/chrony.conf
      #Adding PPS as an optionnal source for chrony
      grep -q 'refclock PPS /dev/pps0 refid PPS lock GNSS' /etc/chrony/chrony.conf || echo '#refclock PPS /dev/pps0 refid PPS lock GNSS' >> /etc/chrony/chrony.conf

      #Overriding chrony.service with custom dependency
      cp /lib/systemd/system/chrony.service /etc/systemd/system/chrony.service
      sed -i s/^After=.*/After=gpsd.service/ /etc/systemd/system/chrony.service

      #disable hotplug
      sed -i 's/^USBAUTO=.*/USBAUTO="false"/' /etc/default/gpsd
      #Setting correct input for gpsd
      sed -i 's/^DEVICES=.*/DEVICES="tcp:\/\/localhost:5015"/' /etc/default/gpsd
      #Adding example for using pps
      grep -qi 'DEVICES="tcp:/localhost:5015 /dev/pps0' /etc/default/gpsd || sed -i '/^DEVICES=.*/a #DEVICES="tcp:\/\/localhost:5015 \/dev\/pps0"' /etc/default/gpsd
      #gpsd should always run, in read only mode
      sed -i 's/^GPSD_OPTIONS=.*/GPSD_OPTIONS="-n -b"/' /etc/default/gpsd
      #Overriding gpsd.service with custom dependency
      cp /lib/systemd/system/gpsd.service /etc/systemd/system/gpsd.service
      sed -i 's/^After=.*/After=str2str_tcp.service/' /etc/systemd/system/gpsd.service
      sed -i '/^# Needed with chrony/d' /etc/systemd/system/gpsd.service
      #Add restart condition
      grep -qi '^Restart=' /etc/systemd/system/gpsd.service || sed -i '/^ExecStart=.*/a Restart=always' /etc/systemd/system/gpsd.service
      grep -qi '^RestartSec=' /etc/systemd/system/gpsd.service || sed -i '/^Restart=always.*/a RestartSec=30' /etc/systemd/system/gpsd.service
      #Add ExecStartPre condition to not start gpsd if str2str_tcp is not running. See https://github.com/systemd/systemd/issues/1312
      grep -qi '^ExecStartPre=' /etc/systemd/system/gpsd.service || sed -i '/^ExecStart=.*/i ExecStartPre=systemctl is-active str2str_tcp.service' /etc/systemd/system/gpsd.service

      #Reload systemd services and enable chrony and gpsd
      systemctl daemon-reload
      systemctl enable gpsd
      #systemctl enable chrony # chrony is already enabled
      #return 0
}

install_rtklib() {
    echo '################################'
    echo 'INSTALLING RTKLIB'
    echo '################################'
    arch_package=$(uname -m)
    #[[ $arch_package == 'x86_64' ]] && arch_package='x86'
    [[ -f /sys/firmware/devicetree/base/model ]] && computer_model=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
    # convert "Raspberry Pi 3 Model B plus rev 1.3" or other Raspi model to the variable "Raspberry Pi"
    [ -n "${computer_model}" ] && [ -z "${computer_model##*'Raspberry Pi'*}" ] && computer_model='Raspberry Pi'
    sbc_array=('Xunlong Orange Pi Zero' 'Raspberry Pi' 'OrangePi Zero3')
    #test if computer_model in sbc_array (https://stackoverflow.com/questions/3685970/check-if-a-bash-array-contains-a-value)
    if printf '%s\0' "${sbc_array[@]}" | grep -Fxqz -- "${computer_model}" \
        && [[ -f "${rtkbase_path}"'/tools/bin/rtklib_b34j/'"${arch_package}"'/str2str' ]] \
        && lsb_release -c | grep -qE 'bullseye|bookworm' \
        && "${rtkbase_path}"'/tools/bin/rtklib_b34j/'"${arch_package}"/str2str --version > /dev/null 2>&1
    then
      echo 'Copying new rtklib binary for ' "${computer_model}" ' - ' "${arch_package}"
      cp "${rtkbase_path}"'/tools/bin/rtklib_b34j/'"${arch_package}"/str2str /usr/local/bin/
      cp "${rtkbase_path}"'/tools/bin/rtklib_b34j/'"${arch_package}"/rtkrcv /usr/local/bin/
      cp "${rtkbase_path}"'/tools/bin/rtklib_b34j/'"${arch_package}"/convbin /usr/local/bin/
    else
      echo 'No binary available for ' "${computer_model}" ' - ' "${arch_package}" '. We will build it from source'
      _compil_rtklib
    fi
}

_compil_rtklib() {
    echo '################################'
    echo 'COMPILING RTKLIB 2.4.3 b34j'
    echo '################################'
    #Get Rtklib 2.4.3 b34j release
    sudo -u "${RTKBASE_USER}" wget -qO - https://github.com/rtklibexplorer/RTKLIB/archive/refs/tags/b34j.tar.gz | tar -xvz
    #Install Rtklib app
    #TODO add correct CTARGET in makefile?
    make --directory=RTKLIB-b34j/app/consapp/str2str/gcc
    make --directory=RTKLIB-b34j/app/consapp/str2str/gcc install
    make --directory=RTKLIB-b34j/app/consapp/rtkrcv/gcc
    make --directory=RTKLIB-b34j/app/consapp/rtkrcv/gcc install
    make --directory=RTKLIB-b34j/app/consapp/convbin/gcc
    make --directory=RTKLIB-b34j/app/consapp/convbin/gcc install
    #deleting RTKLIB
    rm -rf RTKLIB-b34j/
}

_rtkbase_repo(){
    #Get rtkbase repository
    if [[ -n "${1}" ]]; then
      sudo -u "${RTKBASE_USER}" git clone --branch "${1}" --single-branch https://github.com/stefal/rtkbase.git
    else
      sudo -u "${RTKBASE_USER}" git clone https://github.com/stefal/rtkbase.git
    fi
    _add_rtkbase_path_to_environment

}

_rtkbase_release(){
    #Get rtkbase latest release
    sudo -u "${RTKBASE_USER}" wget https://github.com/stefal/rtkbase/releases/latest/download/rtkbase.tar.gz -O rtkbase.tar.gz
    sudo -u "${RTKBASE_USER}" tar -xvf rtkbase.tar.gz
    _add_rtkbase_path_to_environment

}

install_rtkbase_from_repo() {
    echo '################################'
    echo 'INSTALLING RTKBASE FROM REPO'
    echo '################################'
    if [ -d "${rtkbase_path}" ]
    then
      if [ -d "${rtkbase_path}"/.git ]
      then
        echo "RtkBase repo: YES, git pull"
        git -C "${rtkbase_path}" pull
      else
        echo "RtkBase repo: NO, rm release & git clone rtkbase"
        rm -r "${rtkbase_path}"
        _rtkbase_repo "${1}"
      fi
    else
      echo "RtkBase repo: NO, git clone rtkbase"
      _rtkbase_repo "${1}"
    fi
}

install_rtkbase_from_release() {
    echo '################################'
    echo 'INSTALLING RTKBASE FROM RELEASE'
    echo '################################'
    if [ -d "${rtkbase_path}" ]
    then
      if [ -d "${rtkbase_path}"/.git ]
      then
        echo "RtkBase release: NO, rm repo & download last release"
        rm -r "${rtkbase_path}"
        _rtkbase_release
      else
        echo "RtkBase release: YES, rm & deploy last release"
        _rtkbase_release
      fi
    else
      echo "RtkBase release: NO, download & deploy last release"
      _rtkbase_release
    fi
}

install_rtkbase_custom_source() {
    echo '################################'
    echo 'INSTALLING RTKBASE FROM A CUSTOM SOURCE'
    echo '################################'
    if [ -d "${rtkbase_path}" ]
    then
      echo "RtkBase folder already exists. Please clean the system, then retry"
      echo "(Don't forget to remove the systemd services)"
      exit 1
    else
      sudo -u "${RTKBASE_USER}" wget "${1}" -O rtkbase.tar.gz
      sudo -u "${RTKBASE_USER}" tar -xvf rtkbase.tar.gz
      _add_rtkbase_path_to_environment
    fi
}

install_rtkbase_bundled() {
    echo '################################'
    echo 'INSTALLING BUNDLED RTKBASE'
    echo '################################'
    if [ -d "${rtkbase_path}" ]
    then
      echo "RtkBase folder already exists. Please clean the system, then retry"
      echo "(Don't forget to remove the systemd services)"
      #exit 1
    fi
    # Find __ARCHIVE__ marker, read archive content and decompress it
    ARCHIVE=$(awk '/^__ARCHIVE__/ {print NR + 1; exit 0; }' "${0}")
    # Check if there is some content after __ARCHIVE__ marker (more than 100 lines)
    [[ $(sed -n '/__ARCHIVE__/,$p' "${0}" | wc -l) -lt 100 ]] && echo "RTKBASE isn't bundled inside install.sh. Please choose another source" && exit 1  
    sudo -u "${RTKBASE_USER}" tail -n+${ARCHIVE} "${0}" | tar xpJv && \
    _add_rtkbase_path_to_environment
}

_add_rtkbase_path_to_environment(){
    echo '################################'
    echo 'ADDING RTKBASE PATH TO ENVIRONMENT'
    echo '################################'
    if [ -d rtkbase ]
      then
        if grep -q '^rtkbase_path=' /etc/environment
          then
            #Change the path using @ as separator because / is present in $(pwd) output
            sed -i "s@^rtkbase_path=.*@rtkbase_path=$(pwd)\/rtkbase@" /etc/environment
          else
            #Add the path
            echo "rtkbase_path=$(pwd)/rtkbase" >> /etc/environment
        fi
    fi
    rtkbase_path=$(pwd)/rtkbase
    export rtkbase_path
}

rtkbase_requirements(){
    echo '################################'
    echo 'INSTALLING RTKBASE REQUIREMENTS'
    echo '################################'
      # create virtual environnement for rtkbase
      sudo -u "${RTKBASE_USER}" python3 -m venv "${rtkbase_path}"/venv
      python_venv="${rtkbase_path}"/venv/bin/python
      platform=$(uname -m)
      if [[ $platform =~ 'aarch64' ]] || [[ $platform =~ 'x86_64' ]]
        then
          # More dependencies needed for aarch64 as there is no prebuilt wheel on piwheels.org
          apt-get "${APT_TIMEOUT}" install -y libssl-dev libffi-dev || exit 1
      fi      
      # Copying udev rules
      [[ ! -d /etc/udev/rules.d ]] && mkdir /etc/udev/rules.d/
      cp "${rtkbase_path}"/tools/udev_rules/*.rules /etc/udev/rules.d/
      udevadm control --reload && udevadm trigger
      # Copying polkitd rules and add rtkbase group
      "${rtkbase_path}"/tools/install_polkit_rules.sh "${RTKBASE_USER}"
      #Copying settings.conf.default as settings.conf
      if [[ ! -f "${rtkbase_path}/settings.conf" ]]
      then
        cp "${rtkbase_path}/settings.conf.default" "${rtkbase_path}/settings.conf"
      fi
      #Then launch check cpu temp script for OPI zero LTS
      source "${rtkbase_path}/tools/opizero_temp_offset.sh"
      #venv module installation
      sudo -u "${RTKBASE_USER}" "${python_venv}" -m pip install --upgrade pip setuptools wheel  --extra-index-url https://www.piwheels.org/simple
      # install prebuilt wheel for cryptography because it is unavailable on piwheels (2023/01)
      # not needed anymore (2023/11)
      #if [[ $platform == 'armv7l' ]] && [[ $("${python_venv}" --version) =~ '3.7' ]]
      #  then 
      #    sudo -u "${RTKBASE_USER}" "${python_venv}" -m pip install "${rtkbase_path}"/tools/wheel/cryptography-38.0.0-cp37-cp37m-linux_armv7l.whl
      #elif [[ $platform == 'armv6l' ]] && [[ $("${python_venv}" --version) =~ '3.7' ]]
      #  then
      #    sudo -u "${RTKBASE_USER}" "${python_venv}" -m pip install "${rtkbase_path}"/tools/wheel/cryptography-38.0.0-cp37-cp37m-linux_armv6l.whl
      #fi
      sudo -u "${RTKBASE_USER}" "${python_venv}" -m pip install -r "${rtkbase_path}"/web_app/requirements.txt  --extra-index-url https://www.piwheels.org/simple
      #when we will be able to launch the web server without root, we will use
      #sudo -u $(logname) python3 -m pip install -r requirements.txt --user.
      
      #Installing requirements for Cellular modem. Installing them during the Armbian firstrun doesn't work because the network isn't fully up.
      sudo -u "${RTKBASE_USER}" "${rtkbase_path}/venv/bin/python" -m pip install nmcli  --extra-index-url https://www.piwheels.org/simple
      sudo -u "${RTKBASE_USER}" "${rtkbase_path}/venv/bin/python" -m pip install git+https://github.com/Stefal/sim-modem.git

}

install_unit_files() {
    echo '################################'
    echo 'ADDING UNIT FILES'
    echo '################################'
      if [ -d "${rtkbase_path}" ]
      then 
        #Install unit files
        "${rtkbase_path}"/tools/copy_unit.sh --python_path "${rtkbase_path}"/venv/bin/python --user "${RTKBASE_USER}"
        systemctl enable rtkbase_web.service
        systemctl enable rtkbase_archive.timer
        systemctl daemon-reload
        #Add dialout group to user
        usermod -a -G dialout "${RTKBASE_USER}"
      else
        echo 'RtkBase not installed, use option --rtkbase-release or any other rtkbase installation option.'
      fi
}

detect_gnss() {
    echo '################################'
    echo 'USB GNSS RECEIVER DETECTION'
    echo '################################'
      #This function try to detect a gnss receiver and write the port/format inside settings.conf
      #If the receiver is a U-Blox, it will add the TADJ=1 option on all ntrip/rtcm outputs.
      #If there are several receiver, the last one detected will be add to settings.conf.
      for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
          ID_SERIAL=''
          syspath="${sysdevpath%/dev}"
          devname="$(udevadm info -q name -p "${syspath}")"
          if [[ "$devname" == "bus/"* ]]; then continue; fi
          eval "$(udevadm info -q property --export -p "${syspath}")"
          if [[ -z "$ID_SERIAL" ]]; then continue; fi
          if [[ "$ID_SERIAL" =~ (u-blox|skytraq|Septentrio) ]]
          then
            detected_gnss[0]=$devname
            detected_gnss[1]=$ID_SERIAL
            #echo '/dev/'"${detected_gnss[0]}" ' - ' "${detected_gnss[1]}"
            # If /dev/ttyGNSS is a symlink of the detected serial port, we've found the gnss receiver, break the loop.
            # This test is useful with gnss receiver offering several serial ports (like mosaic X5). The Udev rule should symlink the right one with ttyGNSS
            [[ '/dev/ttyGNSS' -ef '/dev/'"${detected_gnss[0]}" ]] && break
          fi
      done
      if [[ ${#detected_gnss[*]} -ne 2 ]]; then
          vendor_and_product_ids=$(lsusb | grep -i "u-blox\|Septentrio" | grep -Eo "[0-9A-Za-z]+:[0-9A-Za-z]+")
          if [[ -z "$vendor_and_product_ids" ]]; then 
            echo 'NO USB GNSS RECEIVER DETECTED'
            echo 'YOU CAN REDETECT IT FROM THE WEB UI'
            #return 1
          else
            devname=$(_get_device_path "$vendor_and_product_ids")
            detected_gnss[0]=$devname
            detected_gnss[1]='u-blox'
            #echo '/dev/'${detected_gnss[0]} ' - ' ${detected_gnss[1]}
          fi
      fi
    # detection on uart port
      if [[ ${#detected_gnss[*]} -ne 2 ]]; then
        echo '################################'
        echo 'UART GNSS RECEIVER DETECTION'
        echo '################################'
        systemctl is-active --quiet str2str_tcp.service && sudo systemctl stop str2str_tcp.service && echo 'Stopping str2str_tcp service'
        for port in ttyS1 serial0 ttyS2 ttyS3 ttyS0; do
            for port_speed in 3000000 921600 115200 57600 38400 19200 9600; do
                echo 'DETECTION ON ' $port ' at ' $port_speed
                # Detect u-blox ZED-F9P receivers
                if [[ $(python3 "${rtkbase_path}"/tools/ubxtool -f /dev/$port -s $port_speed -p MON-VER -w 5 2>/dev/null) =~ 'ZED-F9P' ]]; then
                    detected_gnss[0]=$port
                    detected_gnss[1]='u-blox'
                    detected_gnss[2]=$port_speed
                    #echo 'U-blox ZED-F9P DETECTED ON ' $port ' at ' $port_speed
                    break
                fi

                # Detect Quectel LC29H-BS receivers using nmea.py
                if [[ $(python3 "${rtkbase_path}"/tools/nmea.py --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Version.txt /dev/$port $port_speed 3 2>/dev/null) =~ 'LC29HBS' ]]; then
                    detected_gnss[0]=$port
                    detected_gnss[1]='LC29H-BS'
                    detected_gnss[2]=$port_speed
                    #echo 'Quectel LC29H-BS DETECTED ON ' $port ' at ' $port_speed
                    break
                fi
                sleep 1
            done
            #exit loop if a receiver is detected
            [[ ${#detected_gnss[*]} -eq 3 ]] && break
        done
      fi
      # Test if speed is in detected_gnss array. If not, add the default value.
      [[ ${#detected_gnss[*]} -eq 2 ]] && detected_gnss[2]='115200'
      # If /dev/ttyGNSS is a symlink of the detected serial port, switch to ttyGNSS
      [[ '/dev/ttyGNSS' -ef '/dev/'"${detected_gnss[0]}" ]] && detected_gnss[0]='ttyGNSS'
      # "send" result
      echo '/dev/'"${detected_gnss[0]}" ' - ' "${detected_gnss[1]}"' - ' "${detected_gnss[2]}"

      #Write Gnss receiver settings inside settings.conf
      #Optional argument --no-write-port (here as variable $1) will prevent settings.conf modifications. It will be just a detection without any modification. 
      if [[ ${#detected_gnss[*]} -eq 3 ]] && [[ "${1}" -eq 0 ]]
        then
          echo 'GNSS RECEIVER DETECTED: /dev/'"${detected_gnss[0]}" ' - ' "${detected_gnss[1]}" ' - ' "${detected_gnss[2]}"
          #if [[ ${detected_gnss[1]} =~ 'u-blox' ]]
          #then
          #  gnss_format='ubx'
          #fi
          if [[ -f "${rtkbase_path}/settings.conf" ]]  && grep -qE "^com_port=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists
          then
            #change the com port value/settings inside settings.conf
            sudo -u "${RTKBASE_USER}" sed -i s/^com_port=.*/com_port=\'${detected_gnss[0]}\'/ "${rtkbase_path}"/settings.conf
            sudo -u "${RTKBASE_USER}" sed -i s/^com_port_settings=.*/com_port_settings=\'${detected_gnss[2]}:8:n:1\'/ "${rtkbase_path}"/settings.conf
            
          else
            echo 'settings.conf is missing'
            return 1
          fi
      elif [[ ${#detected_gnss[*]} -ne 3 ]]
        then
          return 1
      fi
}

_get_device_path() {
    id_Vendor=${1%:*}
    id_Product=${1#*:}
    for path in $(find /sys/devices/ -name idVendor | rev | cut -d/ -f 2- | rev); do
        if grep -q "$id_Vendor" "$path"/idVendor; then
            if grep -q "$id_Product" "$path"/idProduct; then
                find "$path" -name 'device' | rev | cut -d / -f 2 | rev
            fi
        fi
    done
}

configure_gnss(){
    echo '################################'
    echo 'CONFIGURE GNSS RECEIVER'
    echo '################################'
      if [ -d "${rtkbase_path}" ]
      then
        source <( grep -v '^#' "${rtkbase_path}"/settings.conf | grep '=' ) 
        systemctl is-active --quiet str2str_tcp.service && sudo systemctl stop str2str_tcp.service
        #if the receiver is a U-Blox F9P, launch the set_zed-f9p.sh. This script will reset the F9P and configure it with the corrects settings for rtkbase
        if [[ $(python3 "${rtkbase_path}"/tools/ubxtool -f /dev/"${com_port}" -s ${com_port_settings%%:*} -p MON-VER) =~ 'ZED-F9P' ]]
        then
          #get F9P firmware release
          firmware=$(python3 "${rtkbase_path}"/tools/ubxtool -f /dev/"${com_port}" -s ${com_port_settings%%:*} -p MON-VER | grep 'FWVER' | awk '{print $NF}')
          echo 'F9P Firmware: ' "${firmware}"
          sudo -u "${RTKBASE_USER}" sed -i s/^receiver_firmware=.*/receiver_firmware=\'${firmware}\'/ "${rtkbase_path}"/settings.conf
          #configure the F9P for RTKBase
          "${rtkbase_path}"/tools/set_zed-f9p.sh /dev/${com_port} ${com_port_settings%%:*} "${rtkbase_path}"/receiver_cfg/U-Blox_ZED-F9P_rtkbase.cfg        && \
          echo 'U-Blox F9P Successfuly configured'                                                                                                          && \
          #now that the receiver is configured, we can set the right values inside settings.conf
          sudo -u "${RTKBASE_USER}" sed -i s/^com_port_settings=.*/com_port_settings=\'115200:8:n:1\'/ "${rtkbase_path}"/settings.conf                      && \
          sudo -u "${RTKBASE_USER}" sed -i s/^receiver=.*/receiver=\'U-blox_ZED-F9P\'/ "${rtkbase_path}"/settings.conf                                      && \
          sudo -u "${RTKBASE_USER}" sed -i s/^receiver_format=.*/receiver_format=\'ubx\'/ "${rtkbase_path}"/settings.conf                                   && \
          #add option -TADJ=1 on rtcm/ntrip_a/ntrip_b/serial outputs
          sudo -u "${RTKBASE_USER}" sed -i s/^ntrip_a_receiver_options=.*/ntrip_a_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf             && \
          sudo -u "${RTKBASE_USER}" sed -i s/^ntrip_b_receiver_options=.*/ntrip_b_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf             && \
          sudo -u "${RTKBASE_USER}" sed -i s/^local_ntripc_receiver_options=.*/local_ntripc_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf   && \
          sudo -u "${RTKBASE_USER}" sed -i s/^rtcm_receiver_options=.*/rtcm_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf                   && \
          sudo -u "${RTKBASE_USER}" sed -i s/^rtcm_client_receiver_options=.*/rtcm_client_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf     && \
          sudo -u "${RTKBASE_USER}" sed -i s/^rtcm_udp_svr_receiver_options=.*/rtcm_udp_svr_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf   && \
          sudo -u "${RTKBASE_USER}" sed -i s/^rtcm_udp_client_receiver_options=.*/rtcm_udp_client_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf   && \
          sudo -u "${RTKBASE_USER}" sed -i s/^rtcm_serial_receiver_options=.*/rtcm_serial_receiver_options=\'-TADJ=1\'/ "${rtkbase_path}"/settings.conf     && \
          #remove SBAS Rtcm message (1107) as it is disabled in the F9P configuration.
          sudo -u "${RTKBASE_USER}" sed -i -r '/^rtcm_/s/1107(\([0-9]+\))?,//' "${rtkbase_path}"/settings.conf                                              && \
          return $?

        elif [[ $(python3 "${rtkbase_path}"/tools/sept_tool.py --port /dev/ttyGNSS_CTRL --baudrate ${com_port_settings%%:*} --command get_model --retry 5) =~ 'mosaic-X5' ]]
        then
          #get mosaic-X5 firmware release
          firmware="$(python3 "${rtkbase_path}"/tools/sept_tool.py --port /dev/ttyGNSS_CTRL --baudrate ${com_port_settings%%:*} --command get_firmware --retry 5)" || firmware='?'
          echo 'Mosaic-X5 Firmware: ' "${firmware}"
          sudo -u "${RTKBASE_USER}" sed -i s/^receiver_firmware=.*/receiver_firmware=\'${firmware}\'/ "${rtkbase_path}"/settings.conf
          #configure the mosaic-X5 for RTKBase
          echo 'Resetting the mosaic-X5 settings....'
          python3 "${rtkbase_path}"/tools/sept_tool.py --port /dev/ttyGNSS_CTRL --baudrate ${com_port_settings%%:*} --command reset --retry 5
          sleep_time=30 ; echo 'Waiting '$sleep_time's for mosaic-X5 reboot' ; sleep $sleep_time
          echo 'Sending settings....'
          python3 "${rtkbase_path}"/tools/sept_tool.py --port /dev/ttyGNSS_CTRL --baudrate ${com_port_settings%%:*} --command send_config_file "${rtkbase_path}"/receiver_cfg/Septentrio_Mosaic-X5.cfg --store --retry 5
          if [[ $? -eq  0 ]]
          then
            echo 'Septentrio Mosaic-X5 successfuly configured'
            systemctl list-unit-files rtkbase_gnss_web_proxy.service &>/dev/null                                                                            && \
            systemctl enable --now rtkbase_gnss_web_proxy.service                                                                                             && \
            sudo -u "${RTKBASE_USER}" sed -i s/^com_port_settings=.*/com_port_settings=\'115200:8:n:1\'/ "${rtkbase_path}"/settings.conf                      && \
            sudo -u "${RTKBASE_USER}" sed -i s/^receiver=.*/receiver=\'Septentrio_Mosaic-X5\'/ "${rtkbase_path}"/settings.conf                                && \
            sudo -u "${RTKBASE_USER}" sed -i s/^receiver_format=.*/receiver_format=\'sbf\'/ "${rtkbase_path}"/settings.conf
            return $?
          elif [[ $(python3 "${rtkbase_path}"/tools/nmea.py --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Version.txt /dev/"${com_port}" ${com_port_settings%%:*} 3 2>/dev/null) =~ 'LC29HBS' ]]; then
            # Factory reset and configure the module
            python3 "${rtkbase_path}"/tools/nmea.py --verbose --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Factory_Defaults.txt /dev/"${com_port}" ${com_port_settings%%:*} 3 >>"${rtkbase_path}"/logs/LC29HBS_Configure.log && \
            python3 "${rtkbase_path}"/tools/nmea.py --verbose --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Set_Baud.txt /dev/"${com_port}" ${com_port_settings%%:*} 3 >>"${rtkbase_path}"/logs/LC29HBS_Configure.log && \
            python3 "${rtkbase_path}"/tools/nmea.py --verbose --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Save.txt /dev/"${com_port}" ${com_port_settings%%:*} 3 >>"${rtkbase_path}"/logs/LC29HBS_Configure.log && \
            python3 "${rtkbase_path}"/tools/nmea.py --verbose --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Reboot.txt /dev/"${com_port}" ${com_port_settings%%:*} 3 >>"${rtkbase_path}"/logs/LC29HBS_Configure.log && \

            # Speed has now been configured to 921600
            speed=921600
            version_str="$(python3 "${rtkbase_path}"/tools/nmea.py --file "${rtkbase_path}"/receiver_cfg/LC29HBS_Version.txt /dev/"${com_port}" ${speed} 3 2>/dev/null)"
            firmware="`echo "$version_str" | cut -d , -f 2`"
            if [[ -z "$version_str" ]]; then
              echo "Could not get LC29HBS version string after rebooting the module, try power cycling the module."
              return 1
            fi
            sudo -u "${RTKBASE_USER}" sed -i s/^receiver_firmware=.*/receiver_firmware=\'${firmware}\'/ "${rtkbase_path}"/settings.conf && \
            sudo -u "${RTKBASE_USER}" sed -i s/^com_port_settings=.*/com_port_settings=\'921600:8:n:1\'/ "${rtkbase_path}"/settings.conf && \
            sudo -u "${RTKBASE_USER}" sed -i s/^receiver=.*/receiver=\'Quectel LC29HBS\'/ "${rtkbase_path}"/settings.conf && \
            sudo -u "${RTKBASE_USER}" sed -i s/^receiver_format=.*/receiver_format=\'rtcm3\'/ "${rtkbase_path}"/settings.conf
            return $?
          else
            echo 'Failed to configure the Gnss receiver'
            return 1
          fi
        else
          echo 'No Gnss receiver has been set. We can'\''t configure'
          return 1
        fi
      else
        echo 'RtkBase not installed, use option --rtkbase-release'
        return 1
      fi
}

detect_usb_modem() {
    echo '################################'
    echo 'SIMCOM A76XX LTE MODEM DETECTION'
    echo '################################'
      #This function try to detect a simcom lte modem (A76XX serie) and write the port inside settings.conf
  MODEM_DETECTED=0
  for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
      ID_MODEL=''
      syspath="${sysdevpath%/dev}"
      devname="$(udevadm info -q name -p "${syspath}")"
      if [[ "$devname" == "bus/"* ]]; then continue; fi
      eval "$(udevadm info -q property --export -p "${syspath}")"
      #if [[ $MINOR != 1 ]]; then continue; fi
      if [[ -z "$ID_MODEL" ]]; then continue; fi
      if [[ "$ID_MODEL" =~ 'A76XX' ]]
      then
        detected_modem[0]=$devname
        detected_modem[1]=$ID_SERIAL
        echo '/dev/'"${detected_modem[0]}" ' - ' "${detected_modem[1]}"
        MODEM_DETECTED=1
      fi
  done
  if [[ $MODEM_DETECTED -eq 1 ]]; then
    return 0
  else
    echo 'No modem detected'
    return 1
  fi
  }

_add_modem_port(){
  if [[ -f "${rtkbase_path}/settings.conf" ]]  && grep -qE "^modem_at_port=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists
  then
    #change the com port value/settings inside settings.conf
    sudo -u "${RTKBASE_USER}" sed -i s\!^modem_at_port=.*\!modem_at_port=\'${MODEM_AT_PORT}\'! "${rtkbase_path}"/settings.conf
  elif [[ -f "${rtkbase_path}/settings.conf" ]]  && ! grep -qE "^modem_at_port=.*" "${rtkbase_path}"/settings.conf #check if settings.conf exists without modem_at_port entry
  then
    printf "[network]\nmodem_at_port='%s'\n" "${MODEM_AT_PORT}"| sudo tee -a "${rtkbase_path}"/settings.conf > /dev/null

  elif [[ ! -f "${rtkbase_path}/settings.conf" ]]
  then
    #create settings.conf with the modem_at_port setting
    echo 'settings.conf is missing'
    return 1
  fi
}

_configure_modem(){
  "${rtkbase_path}"/tools/lte_network_mgmt.sh --connection_rename
  sudo -u "${RTKBASE_USER}" "${rtkbase_path}/venv/bin/python" "${rtkbase_path}"/tools/modem_config.py --config && \
  "${rtkbase_path}"/tools/lte_network_mgmt.sh --lte_priority
}

start_services() {
  echo '################################'
  echo 'STARTING SERVICES'
  echo '################################'
  systemctl daemon-reload
  systemctl enable --now rtkbase_web.service
  systemctl enable --now str2str_tcp.service
  systemctl enable --now configure_gps.service
  systemctl restart gpsd.service
  systemctl restart chrony.service
  systemctl enable --now rtkbase_archive.timer
  grep -qE "^modem_at_port='/[[:alnum:]]+.*'" "${rtkbase_path}"/settings.conf && systemctl enable --now modem_check.timer
  grep -q "receiver='Septentrio_Mosaic-X5'" "${rtkbase_path}"/settings.conf && systemctl enable --now rtkbase_gnss_web_proxy.service
  echo '################################'
  echo 'END OF INSTALLATION'
  echo 'You can open your browser to http://'"$(hostname -I)"
  #If the user isn't already in dialout group, a reboot is 
  #mandatory to be able to access /dev/tty*
  groups "${RTKBASE_USER}" | grep -q "dialout" || echo "But first, Please REBOOT!!!"
  echo '################################'
}

main() {
  # If rtkbase is installed but the OS wasn't restarted, then the system wide
  # rtkbase_path variable is not set in the current shell. We must source it
  # from /etc/environment or set it to the default value "rtkbase":
  
  if [[ -z ${rtkbase_path} ]]
  then
    if grep -q '^rtkbase_path=' /etc/environment
    then
      source /etc/environment
    else 
      export rtkbase_path='rtkbase'
    fi
  fi
  
  # check if there is at least 300MB of free space on the root partition to install rtkbase
  if [[ $(df "$HOME" | awk 'NR==2 { print $4 }') -lt 300000 ]]
  then
    echo 'Available space is lower than 300MB.'
    echo 'Exiting...'
    exit 1
  fi
  
  #display parameters
  #parsing with getopt: https://www.shellscript.sh/tips/getopt/index.html
  ARG_HELP=0
  ARG_USER=0
  ARG_DEPENDENCIES=0
  ARG_RTKLIB=0
  ARG_RTKBASE_RELEASE=0
  ARG_RTKBASE_REPO=0
  ARG_RTKBASE_BLD=0
  ARG_RTKBASE_SRC=0
  ARG_RTKBASE_RQS=0
  ARG_UNIT=0
  ARG_GPSD_CHRONY=0
  ARG_DETECT_GNSS=0
  ARG_NO_WRITE_PORT=0
  ARG_CONFIGURE_GNSS=0
  ARG_DETECT_MODEM=0
  ARG_START_SERVICES=0
  ARG_ALL=0

  PARSED_ARGUMENTS=$(getopt --name install --options hu:drbi:jf:qtgencmsa: --longoptions help,user:,dependencies,rtklib,rtkbase-release,rtkbase-repo:,rtkbase-bundled,rtkbase-custom:,rtkbase-requirements,unit-files,gpsd-chrony,detect-gnss,no-write-port,configure-gnss,detect-modem,start-services,all: -- "$@")
  VALID_ARGUMENTS=$?
  if [ "$VALID_ARGUMENTS" != "0" ]; then
    #man_help
    echo 'Try '\''install.sh --help'\'' for more information'
    exit 1
  fi

  #echo "PARSED_ARGUMENTS is $PARSED_ARGUMENTS"
  eval set -- "$PARSED_ARGUMENTS"
  while :
    do
      case "$1" in
        -h | --help)   ARG_HELP=1                      ; shift   ;;
        -u | --user)   ARG_USER="${2}"                 ; shift 2 ;;
        -d | --dependencies) ARG_DEPENDENCIES=1        ; shift   ;;
        -r | --rtklib) ARG_RTKLIB=1                    ; shift   ;;
        -b | --rtkbase-release) ARG_RTKBASE_RELEASE=1  ; shift   ;;
        -i | --rtkbase-repo) ARG_RTKBASE_REPO="${2}"   ; shift 2 ;;
        -j | --rtkbase-bundled) ARG_RTKBASE_BLD=1      ; shift   ;;
        -f | --rtkbase-custom) ARG_RTKBASE_SRC="${2}"  ; shift 2 ;;
        -q | --rtkbase-requirements) ARG_RTKBASE_RQS=1 ; shift   ;;
        -t | --unit-files) ARG_UNIT=1                  ; shift   ;;
        -g | --gpsd-chrony) ARG_GPSD_CHRONY=1          ; shift   ;;
        -e | --detect-gnss) ARG_DETECT_GNSS=1  ; shift   ;;
        -n | --no-write-port) ARG_NO_WRITE_PORT=1      ; shift   ;;
        -c | --configure-gnss) ARG_CONFIGURE_GNSS=1    ; shift   ;;
        -m | --detect-modem) ARG_DETECT_MODEM=1        ; shift   ;;
        -s | --start-services) ARG_START_SERVICES=1    ; shift   ;;
        -a | --all) ARG_ALL="${2}"                     ; shift 2 ;;
        # -- means the end of the arguments; drop this, and break out of the while loop
        --) shift; break ;;
        # If invalid options were passed, then getopt should have reported an error,
        # which we checked as VALID_ARGUMENTS when getopt was called...
        *) echo "Unexpected option: $1"
          usage ;;
      esac
    done
  cumulative_exit=0
  [ $ARG_HELP -eq 1 ] && man_help
  _check_user "${ARG_USER}" ; echo 'user for RTKBase is: ' "${RTKBASE_USER}"
  #if [ $ARG_USER != 0 ] ;then echo 'user:' "${ARG_USER}"; check_user "${ARG_USER}"; else ;fi
  if [ $ARG_ALL != 0 ] 
  then
    # test if rtkbase source option is correct
    [[ ' release repo url bundled'  =~ (^|[[:space:]])$ARG_ALL($|[[:space:]]) ]] || { echo 'wrong option, please choose release, repo, url or bundled' ; exit 1 ;}
    [[ $ARG_ALL == 'repo' ]] && [[ "${ARG_RTKBASE_REPO}" == "0" ]] && { echo 'you have to specify the branch with --rtkbase-repo' ; exit 1 ;}
    [[ $ARG_ALL == 'url' ]] && [[ "${ARG_RTKBASE_SRC}" == "0" ]] && { echo 'you have to specify the url with --rtkbase-custom' ; exit 1 ;}
    #Okay launching installation
    install_dependencies && \
    case $ARG_ALL in
      release)
        install_rtkbase_from_release
        ;;
      repo)
        install_rtkbase_from_repo "${ARG_RTKBASE_REPO}"
        ;;
      url)
        install_rtkbase_custom_source "${ARG_RTKBASE_SRC}"
        ;;
      bundled)
        # https://www.matteomattei.com/create-self-contained-installer-in-bash-that-extracts-archives-and-perform-actitions/
        install_rtkbase_bundled
        ;;
    esac                      && \
    rtkbase_requirements      && \
    install_rtklib            && \
    install_unit_files        && \
    install_gpsd_chrony
    ret=$?
    [[ $ret != 0 ]] && ((cumulative_exit+=ret))
    detect_gnss               && \
    configure_gnss
    start_services ; ((cumulative_exit+=$?))
    [[ $cumulative_exit != 0 ]] && echo -e '\n\n Warning! Some errors happened during installation!'
    exit $cumulative_exit
 fi

  [ $ARG_DEPENDENCIES -eq 1 ] && { install_dependencies ; ((cumulative_exit+=$?)) ;}
  [ $ARG_RTKLIB -eq 1 ] && { install_rtklib ; ((cumulative_exit+=$?)) ;}
  [ $ARG_RTKBASE_RELEASE -eq 1 ] && { install_rtkbase_from_release && rtkbase_requirements ; ((cumulative_exit+=$?)) ;}
  if [ $ARG_RTKBASE_REPO != 0 ] ; then { install_rtkbase_from_repo "${ARG_RTKBASE_REPO}" && rtkbase_requirements ; ((cumulative_exit+=$?)) ;} ;fi
  [ $ARG_RTKBASE_BLD -eq 1 ] && { install_rtkbase_bundled && rtkbase_requirements ; ((cumulative_exit+=$?)) ;}
  if [ $ARG_RTKBASE_SRC != 0 ] ; then { install_rtkbase_custom_source "${ARG_RTKBASE_SRC}" && rtkbase_requirements ; ((cumulative_exit+=$?)) ;} ;fi
  [ $ARG_RTKBASE_RQS -eq 1 ] && { rtkbase_requirements ; ((cumulative_exit+=$?)) ;}
  [ $ARG_UNIT -eq 1 ] && { install_unit_files ; ((cumulative_exit+=$?)) ;}
  [ $ARG_GPSD_CHRONY -eq 1 ] && { install_gpsd_chrony ; ((cumulative_exit+=$?)) ;}
  [ $ARG_DETECT_GNSS -eq 1 ] &&  { detect_gnss "${ARG_NO_WRITE_PORT}" ; ((cumulative_exit+=$?)) ;}
  [ $ARG_CONFIGURE_GNSS -eq 1 ] && { configure_gnss ; ((cumulative_exit+=$?)) ;}
  [ $ARG_DETECT_MODEM -eq 1 ] && { detect_usb_modem && _add_modem_port && _configure_modem ; ((cumulative_exit+=$?)) ;}
  [ $ARG_START_SERVICES -eq 1 ] && { start_services ; ((cumulative_exit+=$?)) ;}
}

main "$@"
#echo 'cumulative_exit: ' $cumulative_exit
exit $cumulative_exit

__ARCHIVE__

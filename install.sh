#!/bin/bash
BASEDIR=$(dirname "$0")
#dependency
apt-get update 
apt-get install -y git build-essential python3-pip python3-dev python3-setuptools python3-wheel libsystemd-dev dos2unix
#TODO check if the orange pi need:
#sudo apt install python3-wheel and sudo python3 -m pip -U wheel setuptools (or only wheel or only setuptools)
#Get Rtklib 2.4.3 repository
sudo -u $(logname) git clone -b rtklib_2.4.3 --single-branch https://github.com/tomojitakasu/RTKLIB
#Install Rtklib app
#TODO add correct CTARGET in makefile
make --directory=RTKLIB/app/str2str/gcc
make --directory=RTKLIB/app/str2str/gcc install
make --directory=RTKLIB/app/rtkrcv/gcc
make --directory=RTKLIB/app/rtkrcv/gcc install
make --directory=RTKLIB/app/convbin/gcc
make --directory=RTKLIB/app/convbin/gcc install
#deleting RTKLIB
#rm -rf RTKLIB/

#Get rtkbase repository
sudo -u $(logname) git clone -b web_gui --single-branch https://github.com/stefal/rtkbase.git
#as we need to run the web server as root, we need to install the requirements with
#the same user
python3 -m pip install -r rtkbase/web_app/requirements.txt
#when we will be able to launch the web server ithout root, we will use
#sudo -u $(logname) python3 -m pip install -r requirements.txt --user
#Install unit files
rtkbase/copy_unit.sh
systemctl enable rtkbase_web.service
systemctl daemon-reload
#systemctl enable rtkbase_web.service
#systemctl enable rtkbase_web.service



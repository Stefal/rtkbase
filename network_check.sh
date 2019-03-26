#!/bin/bash
#
#Various functions to check the lan state.
#Need more tests on Rpi cards with wifi connections as str2str was not able to connect to a ntrip caster if started before the wifi is up.
#It is not used on my Orange pi zero and its wired LAN.

uart='/dev/ttyS1'
iface='enp0s3'
svr_list='osm.org osm.fr osm.de'
iface_up=0
wan=0

ping_svr()
{
  ping -q -w2 ${1} >/dev/null 2>&1
  if [ ${?} -eq 0 ]
    then local answer=1
    else local answer=0
  fi
  echo ${answer}
}

ping_svr_list()
{

  for addr in ${svr_list}
  do
    if [ $(ping_svr $addr) -eq 1 ]
      then local answer=1
           break
      else local answer=0
    fi
  done
  echo ${answer}
}


is_lan_up()
{
  if $(ip address | grep -Eq ": $iface:.*state UP")
    then local answer=1
    else local anwer=0
  fi
  echo ${answer}
}

is_time_sync()
{
  if $(timedatectl status | grep -q "synchronized: yes")
    then local answer=1
    else local answer=0
  fi
  echo ${answer}
}




waiting_loop()
#parameter 1: function to test
#parameter 2: timeout value

{
  i=0
  while [ $i -le ${2} ]
  do
    if [[ $(${1}) == 1 ]]
      then
        echo 1
        break
    fi
    ((i++))
    sleep 1
  done
}

wl2()
#parameter 1: function to test
#parameter 2: timeout value

{
  i=0
  while [ $i -le ${2} ]
  do
    echo $1
    ((i++))
    sleep 1
  done
}

main()
{
echo 'lan: ' $(waiting_loop is_lan_up 60)
echo 'time sync: ' $(waiting_loop is_time_sync 60)
echo 'wan up: ' $(waiting_loop ping_svr_list 60)
#echo 'wan up: ' $(wl2 ping_svr_list 60)
}

main


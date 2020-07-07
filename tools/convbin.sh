#!/bin/bash
#convert ubx(zip) to rinex
#./convbin.sh ubx.zip directory mount-name 

#go to directory
cd $2
#Run CONVBIN
  echo "- Processing on	"$1
  #find ubx file in zip and extract
  ubx=$(unzip -l $1 "*.ubx" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  echo "- Extract	"$ubx
  unzip -o $1 $ubx
  #get date file, year & create RINEX name
  filedate=$(echo ${1:0:10})
  year2=$(echo ${1:2:2})
  RINEX=$(echo ${filedate}-${3}.${year2}o)
  #run convbin
  echo "- CREATE RINEX	"${RINEX}
  /usr/local/bin/convbin ${ubx} -v 2.11 -r ubx -hm ${3}    \
			-f 2 -y R -y E -y J -y S -y C -y I        \
			-od -os -oi -ot -ti 30 -tt 0 -ro -TADJ=1  \
			-o ${filedate}-${3}.${year2}o
  echo "- RINEX "${RINEX}" is build"
  #remove ubx
  rm $ubx
#store rinex name for python. 
echo -n -e ${RINEX}"\c" > /etc/environment

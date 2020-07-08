#!/bin/bash
#convert ubx(zip) to rinex
#./convbin.sh ubx.zip directory mount-name 

RAW_ARCHIVE=$1
DATA_DIR=$2
MOUNT_NAME=$3

extract_raw_file() {
  ubx=$(unzip -l ${RAW_ARCHIVE} "*.ubx" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  echo "- Extracting	"$ubx
  unzip -o ${RAW_ARCHIVE} $ubx
  return $?
}

convert_to_rinex() {
  echo "- CREATING RINEX	"${RINEX}
    /usr/local/bin/convbin ${ubx} -v 2.11 -r ubx -hm ${MOUNT_NAME}    \
        -f 2 -y R -y E -y J -y S -y C -y I        \
        -od -os -oi -ot -ti 30 -tt 0 -ro -TADJ=1  \
        -o ${filedate}-${MOUNT_NAME}.${year2}o
    return $?
  }

#go to directory
cd ${DATA_DIR}
#Run CONVBIN
  #get date file, year & create RINEX name
  filedate=$(echo ${1:0:10})
  year2=$(echo ${1:2:2})
  RINEX=$(echo ${filedate}-${MOUNT_NAME}.${year2}o)
  echo "- Processing on	"${RAW_ARCHIVE}
  extract_raw_file && convert_to_rinex && echo -n 'rinex_file='${RINEX}
  #remove ubx
  rm $ubx

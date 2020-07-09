#!/bin/bash
#convert zipped raw file to rinex
#./convbin.sh ubx.zip directory mount-name 

RAW_ARCHIVE=$1
DATA_DIR=$2
MOUNT_NAME=$3
RAW_TYPE=$4

extract_raw_file() {
  raw_file=$(unzip -l ${RAW_ARCHIVE} "*.${RAW_TYPE}" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  echo "- Extracting	" "${raw_file}"
  unzip -o ${RAW_ARCHIVE} "${raw_file}"
  return $?
}

convert_to_rinex() {
  echo "- CREATING RINEX	"${RINEX}
    /usr/local/bin/convbin "${raw_file}" -v 2.11 -r ${RAW_TYPE} -hm ${MOUNT_NAME}    \
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
  #remove raw file
  rm "${raw_file}"

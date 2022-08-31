#!/bin/bash
#convert zipped raw file to rinex
#./convbin.sh ubx.zip directory mount-name raw_type

RAW_ARCHIVE=$1
DATA_DIR=$2
MOUNT_NAME=$3
RAW_TYPE=$4
RINEX_TYPE=$5
CONVBIN_PATH=$(type -P convbin)

extract_raw_file() {
  raw_file=$(unzip -l "${RAW_ARCHIVE}" "*.${RAW_TYPE}" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  test $(echo "${raw_file}" | wc -l) -gt 1 && echo 'Error: More than 1 file in the archive' && return 1
  echo "- Extracting	" "${raw_file}"
  unzip -o "${RAW_ARCHIVE}" "${raw_file}"
  return $?
}

# Rinex v2.11 - 30s - GPS
convert_to_rinex_ign() {
  RINEX_FILE=${filedate}'-'${MOUNT_NAME}'.'${year2}'o'
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 2.11 -r "${RAW_TYPE}" -hm "${MOUNT_NAME}"    \
        -f 2 -y R -y E -y J -y S -y C -y I        \
        -od -os -oi -ot -ti 30 -tt 0 -ro -TADJ=1  \
        -o "${RINEX_FILE}"
    return $?
}

# Rinex v3.04 - 30s -  GPS + GLONASS
convert_to_rinex_nrcan() {
  RINEX_FILE=${filedate}'-'${MOUNT_NAME}'.obs'
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}" -hm "${MOUNT_NAME}"    \
        -f 2 -y E -y J -y S -y C -y I        \
        -od -os -oi -ot -ti 30 -tt 0 -ro -TADJ=1  \
        -o "${RINEX_FILE}"
    return $?
}

# Rinex v3.04 - 30s -  GPS + GLONASS + GALILEO + BEIDOU + QZSS + NAVIC + SBAS
convert_to_rinex_full() {
  RINEX_FILE=${filedate}'-'${MOUNT_NAME}'.obs'
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}" -hm "${MOUNT_NAME}"    \
        -f 2 -od -os -oi -ot -ti 30 -tt 0 \
        -ro -TADJ=1  \
        -o "${RINEX_FILE}"
    return $?
}

test -z "${CONVBIN_PATH}" && echo 'Error: Convbin not found' && exit 1
if [[ ${RINEX_TYPE} == 'ign' ]] ; then rnx_conversion_func='convert_to_rinex_ign'
elif [[ ${RINEX_TYPE} == 'nrcan' ]] ; then rnx_conversion_func='convert_to_rinex_nrcan'
elif [[ ${RINEX_TYPE} == 'full' ]] ; then rnx_conversion_func='convert_to_rinex_full'
fi

#go to directory
cd "${DATA_DIR}" || exit
#get date file, year & create RINEX name
filedate=$(echo ${1:0:10})
year2=$(echo ${1:2:2})
RINEX=$(echo "${filedate}"-"${MOUNT_NAME}"."${year2}"o)
#Let's launch the CONVBIN process
echo "- Processing on	""${RAW_ARCHIVE}"
extract_raw_file                  && \
${rnx_conversion_func}            && \
echo -n 'rinex_file='"${RINEX}"
rm "${raw_file}"

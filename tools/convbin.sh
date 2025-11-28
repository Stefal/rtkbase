#!/bin/bash
#convert zipped raw file to rinex
#./convbin.sh ubx.zip directory rinex_type
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source <( grep '=' "${SCRIPT_DIR}"/../settings.conf )
RAW_ARCHIVE=$1
DATA_DIR=$2
MOUNT_NAME=$mnt_name_a
RAW_TYPE=$receiver_format
RINEX_TYPE=$3
CONVBIN_PATH=$(type -P convbin)
ANT_POSITION=$(echo "${position}" | cs2cs  EPSG:4979 EPSG:4978 -f "%.2f" | sed 's/\s/\//g')
RECEIVER="${receiver}"
REC_VERSION="${receiver_firmware}"
REC_OPTION=''
[[ -n $ntrip_a_receiver_options ]] && REC_OPTION="${ntrip_a_receiver_options}"
ANT_TYPE="${antenna_info}"
RTKBASE_VERSION='RTKBase v'"${version}"

extract_raw_file() {
  raw_file=$(unzip -l "${RAW_ARCHIVE}" "*.${RAW_TYPE}" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  test $(echo "${raw_file}" | wc -l) -gt 1 && echo 'Error: There is more than 1 file in this archive' 1>&2 && exit 1
  echo "- Extracting	" "${raw_file}"
  unzip -o "${RAW_ARCHIVE}" "${raw_file}"
  return $?
}

# Rinex v2.11 - 30s - GPS
convert_to_rinex_ign() {
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 2.11 -r "${RAW_TYPE}"       \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"    \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"   \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"        \
        -f 2 -y R -y E -y J -y S -y C -y I             \
        -od -os -oi -ot -ti 30 -tt 0.005                   \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
    return $?
}

convert_to_rinex_ign_bis() {
  echo "- CREATING RINEX " "${RINEX_FILE}"
  args="${raw_file}"' -v 2.11 -r '"${RAW_TYPE}"' -hc '"${RTKBASE_VERSION}"' -hm '"${MOUNT_NAME}"' -hp '"${ANT_POSITION}"' -ha 0000/'"${ANT_TYPE}"' -hr 0000/'"${RECEIVER}"'/'"${REC_VERSION}"' -f 2 -y R -y E -y J -y S -y C -y I -od -os -oi -ot -ti 30 -tt 0 -ro '"${REC_OPTION}"' -o '"${RINEX_FILE}"
  "${CONVBIN_PATH}" "${args}"
    return $?
}
# Rinex v3.04 - 30s -  GPS + GLONASS + GALILEO
convert_to_rinex_nrcan() {
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}"       \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"   \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"   \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"        \
        -f 2 -y J -y S -y C -y I                  \
        -od -os -oi -ot -ti 30 -tt 0                   \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
    return $?
}

# Rinex v3.04 - 30s -  GPS + GLONASS + GALILEO + BEIDOU + QZSS + NAVIC + SBAS
convert_to_rinex_30s_full() {
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}"       \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"   \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"   \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"        \
        -od -os -oi -ot -ti 30 -tt 0                   \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
    return $?
}

# Rinex v3.04 - 1s -  GPS + GLONASS + GALILEO + BEIDOU + QZSS + NAVIC + SBAS
convert_to_rinex_1s_full() {
  echo "- CREATING RINEX " "${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}"       \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"   \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"   \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"        \
        -od -os -oi -ot -ti 1 -tt 0                    \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
    return $?
}

#go to directory
cd "${DATA_DIR}" || exit 1
#get date file, year & create RINEX name
filedate=$(echo ${1:0:10})
year2=$(echo ${1:2:2})

test -z "${CONVBIN_PATH}" && echo 'Error: Convbin not found' && exit 1
if [[ ${RINEX_TYPE} == 'ign' ]] ; then rnx_conversion_func='convert_to_rinex_ign' ; RINEX_FILE=$(echo "${filedate}"-"${MOUNT_NAME}"_"${RINEX_TYPE}"."${year2}"o)
elif [[ ${RINEX_TYPE} == 'nrcan' ]] ; then rnx_conversion_func='convert_to_rinex_nrcan' ; RINEX_FILE=$(echo "${filedate}"-"${MOUNT_NAME}"_"${RINEX_TYPE}".obs)
elif [[ ${RINEX_TYPE} == '30s_full' ]] ; then rnx_conversion_func='convert_to_rinex_30s_full' ; RINEX_FILE=$(echo "${filedate}"-"${MOUNT_NAME}"_"${RINEX_TYPE}".obs)
elif [[ ${RINEX_TYPE} == '1s_full' ]] ; then rnx_conversion_func='convert_to_rinex_1s_full' ; RINEX_FILE=$(echo "${filedate}"-"${MOUNT_NAME}"_"${RINEX_TYPE}".obs)
fi

#Let's launch the CONVBIN process
echo "- Processing on	""${RAW_ARCHIVE}"
file_extension="${RAW_ARCHIVE##*.}"
if [[ $file_extension == 'zip' ]]
  then
    extract_raw_file
  else 
    raw_file="${RAW_ARCHIVE}"
fi
${rnx_conversion_func}
return_code=$?
echo -n 'rinex_file='"${RINEX_FILE}"
[[ $file_extension == 'zip' ]] && rm "${raw_file}"
exit $return_code
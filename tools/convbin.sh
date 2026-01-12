#!/bin/bash
# convert zipped raw file to rinex
# usage: ./convbin.sh <raw_archive_or_rawfile> <data_dir> <rinex_type>

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source <( grep '=' "${SCRIPT_DIR}"/../settings.conf )

RAW_ARCHIVE="${1:?Missing raw archive/raw file argument}"
DATA_DIR="${2:?Missing data dir argument}"
RINEX_TYPE="${3:?Missing rinex_type argument}"

MOUNT_NAME="$mnt_name_a"
RAW_TYPE="$receiver_format"
CONVBIN_PATH="$(type -P convbin || true)"

ANT_POSITION=$(echo "${position}" | cs2cs EPSG:4979 EPSG:4978 -f "%.2f" | sed 's/\s/\//g')
RECEIVER="${receiver}"
REC_VERSION="${receiver_firmware}"
REC_OPTION=''
[[ -n "${ntrip_a_receiver_options:-}" ]] && REC_OPTION="${ntrip_a_receiver_options}"
ANT_TYPE="${antenna_info}"
RTKBASE_VERSION='RTKBase v'"${version}"

test -z "${CONVBIN_PATH}" && echo 'Error: convbin not found in PATH' 1>&2 && exit 1

extract_raw_file() {
  raw_file=$(unzip -l "${RAW_ARCHIVE}" "*.${RAW_TYPE}" | awk '/-----/ {p = ++p % 2; next} p {print $NF}')
  test "$(echo "${raw_file}" | wc -l)" -gt 1 && echo 'Error: There is more than 1 file in this archive' 1>&2 && exit 1
  echo "- Extracting    ${raw_file}"
  unzip -o "${RAW_ARCHIVE}" "${raw_file}"
}

# Determine observation date for convbin -ts/-te (requires YYYY/MM/DD).
# Primary: RAW_ARCHIVE filename starts with YYYY-MM-DD
# Fallback: filesystem mtime of RAW_ARCHIVE
set_obs_date() {
  filedate="${RAW_ARCHIVE:0:10}"     # expected: YYYY-MM-DD
  year2="${RAW_ARCHIVE:2:2}"         # used for RINEX v2 naming

  if [[ "${filedate}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    OBS_DATE="${filedate//-/\/}"     # YYYY/MM/DD
  else
    OBS_DATE="$(date -r "${RAW_ARCHIVE}" +%Y-%m-%d)" # get mtime date (modified date)
    PREV_DATE="$(date -d "${OBS_DATE} -1 day" +%Y-%m-%d)" # previous day of OBS_DATE
    year2="${PREV_DATE:2:2}"
  fi

  export OBS_DATE filedate year2
}

# GPS Time window for the day (convbin default is GPST unless -tu is used)
TS_HMS="00:00:00"
TE_HMS="23:59:30"

# Rinex v2.11 - 30s - GPS
convert_to_rinex_ign() {
  echo "- CREATING RINEX ${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 2.11 -r "${RAW_TYPE}" \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"        \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"        \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"             \
        -f 3 -y R -y E -y J -y S -y C -y I                  \
        -od -os -oi -ot                                     \
        -ti 30 -tt 0.005                                    \
        -ts "${OBS_DATE}" "${TS_HMS}"                       \
        -te "${OBS_DATE}" "${TE_HMS}"                       \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
}

# (kept for reference; fixed to pass args as separate tokens, not one string)
convert_to_rinex_ign_bis() {
  echo "- CREATING RINEX ${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 2.11 -r "${RAW_TYPE}" \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"        \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"        \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"             \
        -f 3 -y R -y E -y J -y S -y C -y I                  \
        -od -os -oi -ot                                     \
        -ti 30 -tt 0                                        \
        -ts "${OBS_DATE}" "${TS_HMS}"                       \
        -te "${OBS_DATE}" "${TE_HMS}"                       \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
}

# Rinex v3.04 - 30s - GPS + GLONASS + GALILEO
convert_to_rinex_nrcan() {
  echo "- CREATING RINEX ${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}" \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"        \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"        \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"             \
        -f 3 -y J -y S -y C -y I                            \
        -od -os -oi -ot                                     \
        -ti 30 -tt 0                                        \
        -ts "${OBS_DATE}" "${TS_HMS}"                       \
        -te "${OBS_DATE}" "${TE_HMS}"                       \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
}

# Rinex v3.04 - 30s - GPS + GLONASS + GALILEO + BEIDOU + QZSS + NAVIC + SBAS
convert_to_rinex_30s_full() {
  echo "- CREATING RINEX ${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}" \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"        \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"        \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"             \
        -od -os -oi -ot                                     \
        -ti 30 -tt 0                                        \
        -ts "${OBS_DATE}" "${TS_HMS}"                       \
        -te "${OBS_DATE}" "${TE_HMS}"                       \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
}

# Rinex v3.04 - 1s - GPS + GLONASS + GALILEO + BEIDOU + QZSS + NAVIC + SBAS
convert_to_rinex_1s_full() {
  echo "- CREATING RINEX ${RINEX_FILE}"
  "${CONVBIN_PATH}" "${raw_file}" -v 3.04 -r "${RAW_TYPE}" \
        -hc "${RTKBASE_VERSION}" -hm "${MOUNT_NAME}"        \
        -hp "${ANT_POSITION}" -ha 0000/"${ANT_TYPE}"        \
        -hr 0000/"${RECEIVER}"/"${REC_VERSION}"             \
        -od -os -oi -ot                                     \
        -ti 1 -tt 0                                         \
        -ts "${OBS_DATE}" "${TS_HMS}"                       \
        -te "${OBS_DATE}" "${TE_HMS}"                       \
        -ro "${REC_OPTION}" -o "${RINEX_FILE}"
}

# go to directory
cd "${DATA_DIR}" || exit 1

# compute dates for naming and time window
set_obs_date

# choose conversion function and output name
case "${RINEX_TYPE}" in
  ign)
    rnx_conversion_func='convert_to_rinex_ign'
    RINEX_FILE="${filedate}-${MOUNT_NAME}_${RINEX_TYPE}.${year2}o"
    ;;
  nrcan)
    rnx_conversion_func='convert_to_rinex_nrcan'
    RINEX_FILE="${filedate}-${MOUNT_NAME}_${RINEX_TYPE}.obs"
    ;;
  30s_full)
    rnx_conversion_func='convert_to_rinex_30s_full'
    RINEX_FILE="${filedate}-${MOUNT_NAME}_${RINEX_TYPE}.obs"
    ;;
  1s_full)
    rnx_conversion_func='convert_to_rinex_1s_full'
    RINEX_FILE="${filedate}-${MOUNT_NAME}_${RINEX_TYPE}.obs"
    ;;
  *)
    echo "Error: unknown rinex_type '${RINEX_TYPE}' (expected: ign|nrcan|30s_full|1s_full)" 1>&2
    exit 1
    ;;
esac

# Launch convbin
echo "- Processing on  ${RAW_ARCHIVE}"

file_extension="${RAW_ARCHIVE##*.}"
if [[ "${file_extension}" == "zip" ]]; then
  extract_raw_file
else
  raw_file="${RAW_ARCHIVE}"
fi

"${rnx_conversion_func}"
return_code=$?

echo -n "rinex_file=${RINEX_FILE}"

[[ "${file_extension}" == "zip" ]] && rm -f "${raw_file}"

exit "${return_code}"

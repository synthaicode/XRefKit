#!/usr/bin/env bash
set -euo pipefail

artifact_dir="$1"
scanner_dir="$(mktemp -d)"
clamav_release="clamav-1.5.4"
installer="clamav-1.5.4.linux.x86_64.deb"
installer_sha256="28d6efc5b4423e7830c3559339552eb53870a9eac51ac4efb37d60530d329886"

curl --fail --location --silent --show-error --retry 2 --max-time 120 \
  "https://github.com/Cisco-Talos/clamav/releases/download/${clamav_release}/${installer}" \
  --output "${scanner_dir}/${installer}"
printf '%s  %s\n' "${installer_sha256}" "${scanner_dir}/${installer}" | sha256sum --check
dpkg-deb --extract "${scanner_dir}/${installer}" "${scanner_dir}/scanner"
clamav_bin="${scanner_dir}/scanner/usr/local/bin"
export LD_LIBRARY_PATH="${scanner_dir}/scanner/usr/local/lib"
export CVD_CERTS_DIR="${scanner_dir}/scanner/usr/local/etc/certs"
export CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

database_dir="${scanner_dir}/database"
mkdir "${database_dir}"
printf 'DatabaseMirror database.clamav.net\nDatabaseDirectory %s\n' "${database_dir}" > "${scanner_dir}/freshclam.conf"
timeout --signal=TERM --kill-after=30s 10m \
  "${clamav_bin}/freshclam" --config-file="${scanner_dir}/freshclam.conf" --stdout --verbose

"${clamav_bin}/clamscan" --database="${database_dir}" --recursive --infected \
  --fail-if-cvd-older-than=1 "${artifact_dir}"

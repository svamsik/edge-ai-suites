#!/bin/bash

SOURCE="src"
CHART="chart"
if [ ! -f "${SOURCE}/secrets/browser.auth" ]; then
  bash ${SOURCE}/secrets/generate_secrets.sh
fi

if [ ! -f .env ]; then
  touch .env
fi

USER_UID=$(stat -c '%u' "${SOURCE}"/* | sort -rn | head -1)
USER_GID=$(stat -c '%g' "${SOURCE}"/* | sort -rn | head -1)

echo "UID=$USER_UID" > .env
echo "GID=$USER_GID" >> .env

if [ ! -d "${SOURCE}/dlstreamer-pipeline-server/videos" ] || [ -z "$(find "${SOURCE}/dlstreamer-pipeline-server/videos" -type f -name "*.ts" 2>/dev/null)" ]; then
  VIDEO_REPO="https://github.com/open-edge-platform/edge-ai-resources.git"
  VIDEO_BRANCH="ashish/si-videos"
  VIDEOS=("1122east_h264.ts" "1122west_h264.ts" "1122north_h264.ts" "1122south_h264.ts")
  VIDEO_DIR="${SOURCE}/dlstreamer-pipeline-server/videos"

  mkdir -p "${VIDEO_DIR}"
  
  # Clone video repository with LFS
  TEMP_DIR=$(mktemp -d)
  git clone --branch ${VIDEO_BRANCH} --depth 1 ${VIDEO_REPO} ${TEMP_DIR}
  cd ${TEMP_DIR}/videos
  git lfs pull
  
  for VIDEO in "${VIDEOS[@]}"; do
    echo "Copying ${VIDEO}..."
    cp "${VIDEO}" "${VIDEO_DIR}/${VIDEO}"
    if [ ! -f "${VIDEO_DIR}/${VIDEO}" ]; then
        echo "Error: Failed to copy ${VIDEO}"
        rm -rf ${TEMP_DIR}
        exit 1
    fi
  done
  
  rm -rf ${TEMP_DIR}
fi

# Copy files to chart
mkdir -p ${CHART}/files
mkdir -p ${CHART}/files/dlstreamer-pipeline-server/user_scripts/gvapython/sscape
mkdir -p ${CHART}/files/webserver
cp -r \
  ${SOURCE}/controller \
  ${SOURCE}/grafana \
  ${SOURCE}/mosquitto \
  ${SOURCE}/node-red \
  ${CHART}/files
cp -r \
  ${SOURCE}/dlstreamer-pipeline-server/user_scripts \
  ${CHART}/files/dlstreamer-pipeline-server
cp \
  ${SOURCE}/dlstreamer-pipeline-server/config.json \
  ${CHART}/files/dlstreamer-pipeline-server/config.json
cp \
  ${SOURCE}/webserver/user_access_config.json \
  ${CHART}/files/webserver/user_access_config.json

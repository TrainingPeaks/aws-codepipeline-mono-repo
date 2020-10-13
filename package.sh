#!/usr/bin/env bash
set -e

. common.sh

sam build

sam package \
    --s3-bucket ${DEPLOY_BUCKET} \
    --s3-prefix ${PREFIX} \
    --output-template-file deploy-template.yaml \
    --force-upload
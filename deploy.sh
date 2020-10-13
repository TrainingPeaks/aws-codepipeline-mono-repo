#!/usr/bin/env bash
set -e

. common.sh

if [[ -z "${WEBHOOK_SECRET}" ]]; then
    echo "WEBHOOK_SECRET env var does not exist and is required"
    exit 13
fi

aws cloudformation deploy \
    --stack-name ${STACK_NAME} \
    --template-file deploy-template.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --s3-prefix ${PREFIX} \
    --parameter-overrides GitHubWebhookSecret="${WEBHOOK_SECRET}" S3StorageBucket=${DEPLOY_BUCKET}

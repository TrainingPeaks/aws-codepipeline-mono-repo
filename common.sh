#!/usr/bin/env bash
set -e

STACK_NAME="MonoRepo-GitHub-CodePipeline"
PREFIX="mono-repo" 

REQUIRED="AWS_SESSION_TOKEN DEPLOY_BUCKET"
for i in $REQUIRED; do
    if [[ -z "${!i}" ]]; then
        echo "${i} env var does not exist and is required"
        exit 13
    fi
done

cd src
### Example
Creates a code pipeline that is executed by a filter function. To create this pipeline:

```sh
aws cloudformation deploy \
    --stack-name MonoRepoTest-S3Based-Example \
    --template-file cp-example-s3-pipeline.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --force-upload \
    --s3-prefix lambda-based/cp-example-pipeline
```

This will create a CloudFormation stack. To create this stack you will need to have deploy the MonoRepoCodePipelineGithubS3 stack in src to the tools account. This will create:

* The stack contains
    * A code pipeline
* This resource which will add a file in S3 called `mono-repo-s3-example-${HASH}.json`
* This config file in S3 will be evaluated by the `MonoRepoCodePipelineGithub-GitHubEventEvalFunction-${HASH}` when a GitHub push event comes in
    * If the event has a file change under `mono-repo-s3-based/` the `mono-repo-s3-example` pipeline will be executed
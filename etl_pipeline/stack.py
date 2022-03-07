from aws_cdk import (
    BundlingOptions,
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as _iam,
    aws_events as _events,
    aws_sqs as _sqs,
    aws_events_targets as _targets,
    aws_s3 as _s3,
    aws_secretsmanager as _secretsmanager,
)
from constructs import Construct


class EtlPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create bucket
        bucket = _s3.Bucket(self, "etl-pipeline-output")

        # Create role with a basic Lambda execution role
        lambda_role = _iam.Role(
            self,
            "etl-pipeline-lambda-role",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="etl-pipeline-lambda-role",
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
        )

        # This will allow Lambda to write to the bucket we defined
        lambda_role.attach_inline_policy(
            _iam.Policy(
                self,
                "etl-pipeline-lambda-s3-write-policy",
                statements=[_iam.PolicyStatement(actions=["s3:PutObject"], resources=[bucket.bucket_arn + "/*"])],
            )
        )

        api_key = _secretsmanager.Secret.from_secret_name_v2(self, "etl-pipeline-api-key", "AlphaVantageApiKey")

        # Define the Lambda function and bundle external dependencies (requires Docker)
        cdk_lambda = _lambda.Function(
            self,
            "etl-pipeline-lambda-function",
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name="etl-pipeline-lambda-function",
            description="Lambda function performing a simple ETL job",
            memory_size=256,
            timeout=Duration.seconds(120),
            code=_lambda.Code.from_asset(
                "./etl_pipeline/lambda",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_8.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            handler="function.handler",
            role=lambda_role,
            environment={"bucket_name": bucket.bucket_name, "api_key": api_key.secret_value.to_string()},
        )

        # Set an EventBridge rule to trigger the function every Monday at 9am UTC
        rule = _events.Rule(
            self,
            "etl-pipeline-rule",
            rule_name="etl-pipeline-rule",
            schedule=_events.Schedule.expression("cron(10 18 ? * MON *)"),
        )
        queue = _sqs.Queue(self, "etl-pipeline-dlq")
        rule.add_target(
            _targets.LambdaFunction(
                cdk_lambda, dead_letter_queue=queue, max_event_age=Duration.minutes(2), retry_attempts=2
            )
        )

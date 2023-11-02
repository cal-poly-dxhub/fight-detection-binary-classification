from email import policy
from attr import attributes
from aws_cdk import (
    # Duration,
    RemovalPolicy,
    Stack,
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_lambda as _lambda,
    aws_s3_notifications as _s3_notify,
    aws_dynamodb as _ddb,
    custom_resources as cr,
    aws_lambda_event_sources as event_sources
 )
from constructs import Construct


class CdkInfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "CdkInfrastructureQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )



        # ----- Lambda -----
        inference_lambda_role = _iam.Role(
            self,
            "inference_lambda_role",
            assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com")
        )

        inference_lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))
        inference_lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRekognitionFullAccess"))
        inference_lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))

        inference_lambda = _lambda.Function(
            self, 
            "inference-function",
            function_name="inference_function",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset("lambda"),
            handler="lambda_handler.lambda_handler",
            role=inference_lambda_role
        )


        # ----- S3 -----
        image_uploads_bucket = _s3.Bucket(
            self, 
            id="image-uploads-bucket",
            bucket_name="image-uploads-bucket",
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # add bucket policy to uploads bucket
        inference_bucket_policy = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=["s3:GetObject"],
            principals=[inference_lambda_role],
            resources=[image_uploads_bucket.bucket_arn + "/*"]
        )
        image_uploads_bucket.add_to_resource_policy(inference_bucket_policy)

        # trigger lambda on s3 upload
        image_uploads_bucket.add_event_notification(
            _s3.EventType.OBJECT_CREATED,
            _s3_notify.LambdaDestination(inference_lambda)
        )
        
        
        # ----- DynamoDB -----
        fight_detection_window_db = _ddb.Table(
            self, 
            id="window-db",
            table_name="window-db",
            partition_key=_ddb.Attribute(name="School", type=_ddb.AttributeType.STRING),
            # sort_key=_ddb.Attribute(name="Camera", type=_ddb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
            # replication_regions=["us-west-1"],
        )
      
        

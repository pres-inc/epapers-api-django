import boto3
AWS_ACCESS_KEY_ID = "AKIAQRGFB6RHGMADFG73"
AWS_SECRET_ACCESS_KEY = "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"
REGION_NAME = "ap-northeast-1"
AWS_S3_BUCKET_NAME = "e-paper-backet-test"
s3_resource = boto3.resource(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
)
bucket = s3_resource.Bucket(AWS_S3_BUCKET_NAME)
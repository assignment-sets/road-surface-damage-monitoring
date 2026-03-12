import os
import aioboto3

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")

# aioboto3 Session factory
session = aioboto3.Session(region_name=AWS_REGION, profile_name=AWS_PROFILE)
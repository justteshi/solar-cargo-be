from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings
from botocore.exceptions import ClientError

class PrivateMediaStorage(S3Boto3Storage):
    default_acl = 'private'
    custom_domain = False

    def url(self, name):
        client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        try:
            # HEAD request to check if the object exists
            client.head_object(Bucket=self.bucket_name, Key=name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Object does not exist
                return None
            else:
                # Other unexpected S3 error
                raise

        # If it exists, generate the presigned URL
        return client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': name},
            ExpiresIn=3600,  # 1 hour
        )
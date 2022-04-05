import boto3
from decouple import config
from fastapi import HTTPException


class S3Service:
    def __init__(self):
        self.key = config("AWS_ACCESS_KEY_ID")
        self.secret = config("AWS_SECRET_KEY")
        self.region = config("AWS_REGION")
        self.bucket = config("AWS_BUCKET_NAME")
        self.s3 = boto3.client(
            service_name="s3",
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region_name=self.region
        )

    def upload(self, file_path, file_name, ext):
        try:
            self.s3.upload_file(
                file_path,
                self.bucket,
                file_name,
                ExtraArgs={"ACL": "public-read", "ContentType": f"image/{ext}"},
            )
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{file_name}"
        except Exception as e:
            raise HTTPException(500, "S3 Error")
            #return "https://fastapi-complaint-system.s3.eu-central-1.amazonaws.com/3a16a027-d7ed-4562-bde6-31af1d7c59b3.jpeg"

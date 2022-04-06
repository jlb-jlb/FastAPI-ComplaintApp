import boto3
from decouple import config


class SESService:
    def __init__(self):
        self.key = config("AWS_ACCESS_KEY_ID")
        self.secret = config("AWS_SECRET_KEY")
        self.region = config("AWS_REGION")
        self.bucket = config("AWS_BUCKET_NAME")
        self.ses = boto3.client(
            service_name="ses",
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region_name=self.region,
        )

    def send_mail(self, subject, to_addresses, text_data):
        body = {"Text": {"Data": text_data, "Charset": "UTF-8"}}
        self.ses.send_email(
            Source="no-reply@competwatch.com",
            Destination={
                "ToAddresses": to_addresses,
                "CcAddresses": [],
                "BccAddresses": [],
            },
            Message={"Subject": {"Data": subject, "Charset": "UTF-8"}, "Body": body},
        )

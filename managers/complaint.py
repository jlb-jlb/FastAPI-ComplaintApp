import os
import uuid

import boto3
from decouple import config

from constants import TEMP_FILE_FOLDER
from db import database
from models import complaint, RoleType, State
from services.s3 import S3Service
from services.ses import SESService
from utils import helpers

s3 = S3Service()
ses = SESService()


class ComplaintManager:
    @staticmethod
    async def get_complaints(user):
        q = complaint.select()
        if user["role"] == RoleType.complainer:
            q = q.where(complaint.c.complainer_id == user["id"])
        elif user["role"] == RoleType.approver:
            q = q.where(complaint.c.state == State.pending)
        return await database.fetch_all(q)

    @staticmethod
    async def create_complaint(complaint_data, user):
        complaint_data["complainer_id"] = user["id"]
        encoded_photo = complaint_data.pop("encoded_photo")
        extension = complaint_data.pop("extension")
        name = f"{uuid.uuid4()}.{extension}"
        path = os.path.join(TEMP_FILE_FOLDER, name)
        helpers.decode_photo(path, encoded_photo)
        complaint_data["photo_url"] = s3.upload(path, name, extension)
        os.remove(path)
        id_ = await database.execute(complaint.insert().values(complaint_data))
        return await database.fetch_one(complaint.select().where(complaint.c.id == id_))
    """
        region = config("AWS_REGION")
        key = config("AWS_ACCESS_KEY_ID")
        secret = config("AWS_SECRET_KEY")
        bucket = config("AWS_BUCKET_NAME")
        # file_path = "/home/jlb/PycharmProjects/fastAPI-ComplaintAPP/temp_files/3b9b89f9-5924-41f2-9fcd-86574868dc6d.jpeg"

        extension = "jpeg"
        file_encoded = "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"
        name = f"{uuid.uuid4()}.{extension}"
        # name = "3b9b89f9-5924-41f2-9fcd-86574868dc6d.jpeg"

        file_path = os.path.join(TEMP_FILE_FOLDER, name)

        helpers.decode_photo(file_path, file_encoded)

        s3 = boto3.client(
            service_name="s3",
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            region_name=region
        )
        try:
            x = s3.upload_file(
                file_path,
                bucket,
                name,
                ExtraArgs={"ACL": "public-read", "ContentType": f"image/{extension}"}
            )
        except Exception as e:
            name = "3a16a027-d7ed-4562-bde6-31af1d7c59b3.jpeg"

            print(e)
    """

    @staticmethod
    async def delete_complaint(complaint_id):
        await database.execute(complaint.delete().where(complaint.c.id == complaint_id))

    @staticmethod
    async def approve(id_):
        await database.execute(
            complaint.update()
            .where(complaint.c.id == id_)
            .values(status=State.approved)
        )
        ses.send_mail(
            "Complaint approved!",  # title
            ["joscha.bisping@gmail.com"],  # for now hardcoded # recipient
            "Congrats your claim is approved. Check your bank account in 2 days"  # Body
        )

    @staticmethod
    async def reject(id_):
        await database.execute(
            complaint.update()
            .where(complaint.c.id == id_)
            .values(status=State.rejected)
        )

import os
import uuid


from constants import TEMP_FILE_FOLDER
from db import database
from models import complaint, RoleType, State, transaction
from services.s3 import S3Service
from services.ses import SESService
from services.wise import WiseService
from utils import helpers

s3 = S3Service()
ses = SESService()
wise = WiseService()


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
        async with database.transaction() as tconn:  # ensure that a transaction is complete or not happening
            id_ = await tconn._connection.execute(complaint.insert().values(complaint_data))
            # raise Exception  # test
            await ComplaintManager.issue_transaction(
                tconn,
                complaint_data["amount"],
                f"{user['first_name']} {user['last_name']}",
                user["iban"],
                id_,
            )
        return await database.fetch_one(complaint.select().where(complaint.c.id == id_))

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
        # fetch Transaction Data from Database
        transaction_data = await database.fetch_one(
            transaction.select().where(transaction.c.complaint_id == id_)
        )
        wise.fund_transfer(transaction_data["transfer_id"])
        ses.send_mail(
            "Complaint approved!",  # title
            ["joscha.bisping@gmail.com"],  # for now hardcoded # recipient
            "Congrats your claim is approved. Check your bank account in 2 days",  # Body
        )

    @staticmethod
    async def reject(id_):
        transaction_data = await database.fetch_one(
            transaction.select().where(transaction.c.complaint_id == id_)
        )
        wise.cancel_funds(transaction_data["transfer_id"])
        await database.execute(
            complaint.update()
            .where(complaint.c.id == id_)
            .values(status=State.rejected)
        )
        ses.send_mail(
            "Complaint rejected!",  # title
            ["joscha.bisping@gmail.com"],  # for now hardcoded # recipient
            "Unfortunately we we cannot approve your complaint.",  # Body
        )

    @staticmethod
    async def issue_transaction(tconn, amount, full_name, iban, complaint_id):
        quote_id = wise.create_quote(amount)
        recipient_id = wise.create_recipient_account(full_name, iban)
        transfer_ident = wise.create_transfer(recipient_id, quote_id)
        # resp = wise.fund_transfer(transfer_ident) # first it needs approval from approver
        data = {
            "quote_id": quote_id,
            "transfer_id": transfer_ident,
            "target_account_id": str(recipient_id),
            "amount": amount,
            "complaint_id": complaint_id,
        }
        await tconn._connection.execute(transaction.insert().values(**data))

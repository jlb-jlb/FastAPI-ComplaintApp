import json
import uuid

import requests
from decouple import config
from fastapi import HTTPException


class WiseService:
    def __init__(self):
        self.main_url = config("WISE_URL")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config('WISE_TOKEN')}",
        }
        self.profile_id = self._get_profile_id()

    def _get_profile_id(self):
        url = config("WISE_API_GET_PROFILES")
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            resp = resp.json()
            return [el["id"] for el in resp if el["type"] == "personal"][0]
        print(resp)
        raise HTTPException(500, "Payment provider is not available at the moment")

    def create_quote(self, amount):
        url = config("WISE_API_POST_QUOTES")
        data = {
            "sourceCurrency": "EUR",
            "targetCurrency": "EUR",
            # "sourceAmount": 100,
            "targetAmount": amount,
            "profile": self.profile_id
        }
        resp = requests.post(url, headers=self.headers, data=json.dumps(data))
        return self._check_status_id(resp)

    def create_recipient_account(self, full_name, iban):
        url = config("WISE_API_POST_ACCOUNTS")
        data = {
                "currency": "EUR",
                "type": "iban",
                "profile": self.profile_id,
                "accountHolderName": full_name,
                "legalType": "PRIVATE",
                "details": {
                    "iban": iban,
                }
        }
        resp = requests.post(url, headers=self.headers, data=json.dumps(data))
        return self._check_status_id(resp)

    def create_transfer(self, target_account_id, quote_id):
        url = config("WISE_API_POST_TRANSFERS")
        customer_transaction_id = str(uuid.uuid1())  # use 4
        data = {
            "targetAccount": target_account_id,
            "quoteUuid": quote_id,
            "customerTransactionId": customer_transaction_id,
            "details": {
                "reference": "customer refund",
                "transferPurpose": "verification.transfers.purpose.pay.bills",
                "sourceOfFunds": "verification.source.of.funds.other"
            },
        }
        resp = requests.post(url, headers=self.headers, data=json.dumps(data))
        return self._check_status_id(resp)

    def fund_transfer(self, transfer_id):
        url = self.main_url + f"/v3/profiles/{self.profile_id}/transfers/{transfer_id}/payments"
        data = {
            "type": "BALANCE"
        }
        resp = requests.post(url, headers=self.headers, data=json.dumps(data))
        return self._check_status_id(resp, code=201, ident="balanceTransactionId")

    @staticmethod
    def _check_status(resp, code=200):
        """Checks if statuscode == 200 and returns the FULL response object"""
        if resp.status_code == code:
            resp = resp.json()
            return resp
        print(resp)
        raise HTTPException(500, "Payment provider is not available at the moment")

    @staticmethod
    def _check_status_id(resp, code=200, ident="id"):
        """Checks if status code == 200 and returns the id of the response object"""
        if resp.status_code == code:
            resp = resp.json()
            return resp[ident]
        print(resp)
        raise HTTPException(status_code=500, detail="Payment provider is not available at the moment")


if __name__ == "__main__":
    wise = WiseService()
    quote_idx = wise.create_quote(10.11)
    recipient_id = wise.create_recipient_account("Joscha Xylophon", "DE89370400440532013000")
    transfer_id = wise.create_transfer(recipient_id, quote_idx)
    res = wise.fund_transfer(transfer_id)
    a = 5

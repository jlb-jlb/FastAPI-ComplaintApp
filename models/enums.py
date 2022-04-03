import enum


class RoleType(enum.Enum):
    approver = "approver"
    complainer = "compplainer"
    admin = "admin"


class State(enum.Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"


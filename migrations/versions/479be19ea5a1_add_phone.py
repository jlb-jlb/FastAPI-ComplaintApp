"""Add phone

Revision ID: 479be19ea5a1
Revises: 88e82928e5b7
Create Date: 2022-03-29 01:03:13.999793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '479be19ea5a1'
down_revision = '88e82928e5b7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'phone')
    # ### end Alembic commands ###

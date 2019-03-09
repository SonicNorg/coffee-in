"""Ondelete added

Revision ID: 3a4b713c7c2b
Revises: fc5878f41606
Create Date: 2019-03-09 09:27:02.472715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4b713c7c2b'
down_revision = 'fc5878f41606'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'coffee_prices', type_='foreignkey')
    op.drop_constraint(None, 'coffee_prices', type_='foreignkey')
    op.create_foreign_key(None, 'coffee_prices', 'coffee_sorts', ['coffee_type_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'coffee_prices', 'prices', ['price_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'coffee_prices', type_='foreignkey')
    op.drop_constraint(None, 'coffee_prices', type_='foreignkey')
    op.create_foreign_key(None, 'coffee_prices', 'coffee_sorts', ['coffee_type_id'], ['id'])
    op.create_foreign_key(None, 'coffee_prices', 'prices', ['price_id'], ['id'])
    # ### end Alembic commands ###

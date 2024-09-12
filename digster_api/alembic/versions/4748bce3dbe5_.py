"""empty message

Revision ID: 4748bce3dbe5
Revises: a3cf474a2448
Create Date: 2024-09-05 18:36:46.795676

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4748bce3dbe5'
down_revision = 'a3cf474a2448'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('albums', sa.Column('fetched_genres_date', sa.DateTime(), nullable=True))
    op.add_column('albums', sa.Column('fetched_colors_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('albums', 'fetched_colors_date')
    op.drop_column('albums', 'fetched_genres_date')
    # ### end Alembic commands ###
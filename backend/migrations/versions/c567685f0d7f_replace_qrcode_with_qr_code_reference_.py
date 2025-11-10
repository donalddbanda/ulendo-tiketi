"""Replace qrcode with qr_code_reference system

Revision ID: c567685f0d7f
Revises: 769a273b9ddd
Create Date: 2025-11-10 13:04:33.239604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c567685f0d7f'
down_revision = '769a273b9ddd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        # Remove old column
        batch_op.drop_column('qrcode')
        
        # Add new columns
        batch_op.add_column(sa.Column('qr_code_reference', sa.String(length=100), nullable=True, unique=True))
        batch_op.add_column(sa.Column('qr_code_reference_status', sa.String(length=20), nullable=False, server_default='unused'))
        batch_op.add_column(sa.Column('boarded_at', sa.DateTime(), nullable=True))
        
        # Add indexes
        batch_op.create_index('ix_bookings_qr_code_reference', ['qr_code_reference'], unique=True)
        batch_op.create_index('ix_bookings_qr_code_reference_status', ['qr_code_reference_status'], unique=False)


def downgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_index('ix_bookings_qr_code_reference_status')
        batch_op.drop_index('ix_bookings_qr_code_reference')
        batch_op.drop_column('boarded_at')
        batch_op.drop_column('qr_code_reference_status')
        batch_op.drop_column('qr_code_reference')
        batch_op.add_column(sa.Column('qrcode', sa.String(length=100), nullable=False, unique=True))
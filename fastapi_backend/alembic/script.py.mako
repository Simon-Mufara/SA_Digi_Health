"""${message}"""

revision = ${up_revision!r}
down_revision = ${down_revision!r}
branch_labels = ${branch_labels!r}
depends_on = ${depends_on!r}

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
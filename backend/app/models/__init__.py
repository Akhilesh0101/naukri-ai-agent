"""Import all models so Alembic autogenerate and Base.metadata see them."""
from app.models.profile import UserProfile  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.source import JobSource, SyncHistory  # noqa: F401
from app.models.job import Job, MatchResult  # noqa: F401
from app.models.application import Application, ApplicationAttempt  # noqa: F401
from app.models.activity import ActivityLog  # noqa: F401

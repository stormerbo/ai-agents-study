"""Explicit local-only configuration; never load the site's provider secrets."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls):
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL is required; use the local Compose service")
        return cls(database_url=dsn)


# Public synthetic credentials, solely for loopback teaching deployments.
# The token chooses identity; roles and active membership are read from PostgreSQL.
DEMO_TOKENS = {
    "dev-alice": ("tenant-a", "alice"),
    "dev-bob": ("tenant-a", "bob"),
    "dev-approver": ("tenant-a", "approver"),
    "dev-operator": ("tenant-a", "operator"),
    "dev-mallory": ("tenant-b", "mallory"),
}

"""
<<<<<<< HEAD:cosmos/integration/email/__init__.py
cosmos Email Integration Package
=======
Farnsworth Email Integration Package
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/email/__init__.py

"Good news, everyone! I can now manage your email across all providers!"

Comprehensive email integration for Office 365, Google Workspace, and more.
"""

<<<<<<< HEAD:cosmos/integration/email/__init__.py
from cosmos.integration.email.office365 import (
    Office365Integration,
    office365_integration,
)
from cosmos.integration.email.google_workspace import (
    GoogleWorkspaceIntegration,
    google_workspace_integration,
)
from cosmos.integration.email.mailbox_filter import (
=======
from farnsworth.integration.email.office365 import (
    Office365Integration,
    office365_integration,
)
from farnsworth.integration.email.google_workspace import (
    GoogleWorkspaceIntegration,
    google_workspace_integration,
)
from farnsworth.integration.email.mailbox_filter import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/integration/email/__init__.py
    MailboxFilter,
    FilterRule,
    mailbox_filter,
)


__all__ = [
    "Office365Integration",
    "office365_integration",
    "GoogleWorkspaceIntegration",
    "google_workspace_integration",
    "MailboxFilter",
    "FilterRule",
    "mailbox_filter",
]

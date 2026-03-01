"""
<<<<<<< HEAD:cosmos/cicd/__init__.py
cosmos CI/CD Pipeline Management
=======
Farnsworth CI/CD Pipeline Management
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/cicd/__init__.py

"Good news, everyone! The build passed!"

Comprehensive CI/CD integration for GitHub Actions, GitLab CI, and Jenkins.
"""

<<<<<<< HEAD:cosmos/cicd/__init__.py
from cosmos.cicd.pipeline_manager import (
=======
from farnsworth.cicd.pipeline_manager import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/cicd/__init__.py
    PipelineManager,
    Pipeline,
    PipelineRun,
    PipelineStatus,
)
<<<<<<< HEAD:cosmos/cicd/__init__.py
from cosmos.cicd.github_actions import GitHubActionsManager
from cosmos.cicd.gitlab_ci import GitLabCIManager
from cosmos.cicd.jenkins_manager import JenkinsManager
=======
from farnsworth.cicd.github_actions import GitHubActionsManager
from farnsworth.cicd.gitlab_ci import GitLabCIManager
from farnsworth.cicd.jenkins_manager import JenkinsManager
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/cicd/__init__.py

__all__ = [
    "PipelineManager",
    "Pipeline",
    "PipelineRun",
    "PipelineStatus",
    "GitHubActionsManager",
    "GitLabCIManager",
    "JenkinsManager",
]

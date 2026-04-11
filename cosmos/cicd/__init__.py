"""
cosmos CI/CD Pipeline Management

"Good news, everyone! The build passed!"

Comprehensive CI/CD integration for GitHub Actions, GitLab CI, and Jenkins.
"""

from cosmos.cicd.pipeline_manager import (
    PipelineManager,
    Pipeline,
    PipelineRun,
    PipelineStatus,
)
from cosmos.cicd.github_actions import GitHubActionsManager
from cosmos.cicd.gitlab_ci import GitLabCIManager
from cosmos.cicd.jenkins_manager import JenkinsManager

__all__ = [
    "PipelineManager",
    "Pipeline",
    "PipelineRun",
    "PipelineStatus",
    "GitHubActionsManager",
    "GitLabCIManager",
    "JenkinsManager",
]

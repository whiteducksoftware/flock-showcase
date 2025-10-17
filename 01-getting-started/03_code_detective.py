"""
Getting Started: Code Detective

This example demonstrates analyzing structured data (bug reports) and generating
detailed diagnoses with multiple output fields.

🎛️  CONFIGURATION: Set USE_DASHBOARD to switch between CLI and Dashboard modes
"""

import asyncio
from datetime import datetime

from pydantic import BaseModel, Field

from flock.orchestrator import Flock
from flock.registry import flock_type

# ============================================================================
# 🎛️  CONFIGURATION: Switch between CLI and Dashboard modes
# ============================================================================
USE_DASHBOARD = False  # Set to True for dashboard mode, False for CLI mode
# ============================================================================


@flock_type
class BugReport(BaseModel):
    title: str
    description: str
    reporter: str
    timestamp: datetime = Field(default_factory=datetime.now)


@flock_type
class BugDiagnosis(BaseModel):
    severity: str
    root_cause: str
    affected_components: list[str]
    suggested_fix: str
    requires_hotfix: bool
    confidence_score: float = Field(ge=0.0, le=1.0)


flock = Flock()

code_detective = (
    flock.agent("code_detective")
    .description("Analyzes bug reports and provides structured diagnoses")
    .consumes(BugReport)
    .publishes(BugDiagnosis)
)


async def main_cli():
    """CLI mode: Run agents and display results in terminal"""
    bug_reports = [
        BugReport(
            title="App crashes when user clicks submit",
            description="Users report that clicking submit on the contact form crashes the app. "
            "Error: 'TypeError: Cannot read property of undefined'. Started after yesterday's deployment.",
            reporter="sarah.dev@company.com",
        ),
        BugReport(
            title="Login page not loading",
            description="Login page shows white screen. Console shows 404 for login.css. "
            "Only in production, works locally.",
            reporter="mike.frontend@company.com",
        ),
    ]

    await flock.publish_many(bug_reports)
    await flock.run_until_idle()

    diagnoses = await flock.store.get_by_type(BugDiagnosis)

    for i, diagnosis in enumerate(diagnoses):
        print(f"\n📊 DIAGNOSIS {i + 1}:")
        print(f"   Severity: {diagnosis.severity}")
        print(f"   Root Cause: {diagnosis.root_cause}")
        print(f"   Components: {', '.join(diagnosis.affected_components)}")
        print(f"   Fix: {diagnosis.suggested_fix}")
        print(f"   Hotfix: {diagnosis.requires_hotfix}")
        print(f"   Confidence: {diagnosis.confidence_score:.2f}")


async def main_dashboard():
    """Dashboard mode: Serve with interactive web interface"""
    await flock.serve(dashboard=True)


async def main():
    if USE_DASHBOARD:
        await main_dashboard()
    else:
        await main_cli()


if __name__ == "__main__":
    asyncio.run(main())

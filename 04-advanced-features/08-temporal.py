import asyncio
from datetime import timedelta

from flock.core import Flock, FlockFactory
from flock.routers.default.default_router import DefaultRouterConfig
from flock.workflow.temporal_config import (
    TemporalActivityConfig,
    TemporalRetryPolicyConfig,
    TemporalWorkflowConfig,
)


async def main():
    workflow_config = TemporalWorkflowConfig(
        task_queue="flock-test-queue",
        workflow_execution_timeout=timedelta(minutes=10),
        default_activity_retry_policy=TemporalRetryPolicyConfig(
            maximum_attempts=2
        ),
    )

    flock = Flock(
        enable_temporal=True,
        enable_logging=True,
        temporal_config=workflow_config,
    )

    agent = FlockFactory.create_default_agent(
        name="my_presentation_agent",
        input="topic",
        output="funny_title, funny_slide_headers",
    )

    flock.add_agent(agent)

    content_agent_retry_policy = TemporalRetryPolicyConfig(
        maximum_attempts=4,
        initial_interval=timedelta(seconds=2),
        non_retryable_error_types=["ValueError"],
    )
    content_agent_activity_config = TemporalActivityConfig(
        start_to_close_timeout=timedelta(minutes=1),
        retry_policy=content_agent_retry_policy,
    )

    content_agent = FlockFactory.create_default_agent(
        name="content_agent",
        input="funny_title, funny_slide_headers",
        output="funny_slide_content",
        temporal_activity_config=content_agent_activity_config,
    )

    flock.add_agent(content_agent)

    agent.add_component(DefaultRouterConfig(hand_off="content_agent"))

    print(
        f"Starting Flock run on Temporal task queue: {workflow_config.task_queue}"
    )

    result = await flock.run_async(
        start_agent="my_presentation_agent",
        input={
            "topic": "A presentation about apples in which cute kitten faces are carved in"
        },
    )

    print("\n--- Result ---")
    print(result)


if __name__ == "__main__":
    print(
        "Ensure a Temporal worker is running and listening on the specified task queue(s)."
    )
    asyncio.run(main())

from opik.evaluation.metrics import (
    Contains,
)

from flock.core import FlockFactory
from flock.core.evaluation.utils import evaluate_with_opik

qa_agent = FlockFactory.create_default_agent(
    name="my_qa_agent",
    input="query",
    output="short_single_word_answer",
    model="azure/gpt-4.1-mini",
    no_output=True,
)

evaluate_with_opik(
    dataset="smolagents/benchmark-v1",
    dataset_name="smolagents/benchmark-v1",
    experiment_name="smolagents_gpt-4.1-mini",
    start_agent=qa_agent,
    input_mapping={"question": "query"},
    answer_mapping={"true_answer": "short_single_word_answer"},
    metrics=[Contains()],
)

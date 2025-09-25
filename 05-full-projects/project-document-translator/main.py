from flock.core import Flock, FlockFactory, flock_type
from pydantic import BaseModel, Field
from flock.core.logging.logging import get_logger as _get_logger
from translation_service import translate_document_sync, translate_pdf_inplace
# ---------------------------------------------------------------------------
_logger = _get_logger("document_translator")

@flock_type
class DocumentTranslator(BaseModel):
    name: str = Field(..., description="Name of the document")
    description: str = Field(..., description="Description of the document")
    input_language: str = Field(..., description="Input language of the document")
    output_language: str = Field(..., description="Output language of the document")
    input_pages: list[str] = Field(..., description="Input pages of the document")
    output_pages: list[str] = Field(..., description="The translated output pages of the document. Decided by the agent.")
    unsure_translations: list[str] = Field(..., description="The unsure translations of the document. Decided by the agent.")



flock = Flock(model="openai/gpt-4.1")

translation_agent = FlockFactory.create_default_agent(
    name="translation_agent",
    description="An agent that translates a document from one language to another."
    "This agent uses translate_pdf_inplace for pdf files and translate_document_sync for other file types",
    input="path: str, output_language: str, output_dir: str",
    output="output_path: str | formatted as a markdown link",
    tools=[translate_document_sync, translate_pdf_inplace],
    stream=True,
    temperature=1.0,
    max_tokens=120000,
)

flock.add_agent(translation_agent)

path = "data/1706.03762v7.pdf"
output_language = "Deutsch"
output_dir = "data_translated/"


result = flock.run(
    agent=translation_agent,
    input={
        "path": path,
        "output_language": output_language,
        "output_dir": output_dir,
    },
)
print(result.output_path)



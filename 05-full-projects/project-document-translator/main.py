from flock.core import Flock, FlockFactory, flock_type, flock_tool
from pydantic import BaseModel, Field
from pathlib import Path
from flock.core.logging.logging import get_logger as _get_logger
import argparse
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Optional
import requests
# ---------------------------------------------------------------------------
_logger = _get_logger("document_translator")

@flock_tool
def convert_pdf_to_markdown(file_path: str) -> str:
    result = "Could not convert PDF to Markdown. Exception occured."
    try:
        # wrap import in try-catch
        import pymupdf
        import pymupdf4llm  # type: ignore - not in stubs

        doc = pymupdf.open(file_path)
        md_text = pymupdf4llm.to_markdown(doc, show_progress=True)
        Path("extracted.md").write_bytes(md_text.encode())
        result = md_text
    except ImportError as import_error:
        # If import failed, mark it in the docs.
        message = (
            "Tool: '_convert_pdf_to_markdown': "
            f"ImportError: {import_error} "
            "Please make sure pymupdf and pymupdf4llm are installed and available for import."
        )
        _logger.error(message=message)

    except Exception as e:
        # catch-all
        message = f"Tool: '_convert_pdf_to_markdown': Exception occured: {e} "
        _logger.error(message=message)

    finally:
        # return *something*
        # so the application does not crash
        return result
    
@flock_tool
def save_translated_pages(text: str, file_path: str) -> str:
    with open(file_path, "w") as f:
        f.write(text)
    return "File saved successfully"


SYNC_API_VERSION = "2024-05-01"  # per MS docs

# Env vars (no placeholders/mocks in code)
#   AZURE_TRANSLATOR_ENDPOINT = e.g. https://<your-instance>.cognitiveservices.azure.com
#   AZURE_TRANSLATOR_KEY      = Translator key
#   AZURE_TRANSLATOR_REGION   = optional, only if your resource/endpoint requires region header

def _guess_content_type(p: Path) -> str:
    ctype, _ = mimetypes.guess_type(p.name)
    return ctype or "application/octet-stream"

def _backoff_sleep(attempt: int) -> None:
    time.sleep(min(20, 2 ** attempt))


@flock_tool
def translate_document_sync(
    input_path: str,
    target_language_iso_code: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Translate a single Office document using Azure AI Translator (synchronous API).
    Returns the output file path that was written.

    Raises RuntimeError on non-200 response.
    """

    timeout_s=600
    max_retries=4
    glossary_path = None
    source_language = None

    endpoint = os.environ.get("AZURE_TRANSLATOR_ENDPOINT", "").rstrip("/")
    key = os.environ.get("AZURE_TRANSLATOR_KEY")
    region = os.environ.get("AZURE_TRANSLATOR_REGION")  # optional

    if not endpoint or not key:
        raise RuntimeError("Missing AZURE_TRANSLATOR_ENDPOINT or AZURE_TRANSLATOR_KEY.")

    src = Path(input_path)
    if not src.is_file():
        raise RuntimeError(f"Input file not found: {input_path}")

    # Sync API limit is 10 MB per file
    size_bytes = src.stat().st_size
    if size_bytes > 10 * 1024 * 1024:
        raise RuntimeError(
            f"File is {size_bytes/1024/1024:.2f} MB. "
            "Synchronous API limit is 10 MB. Use the batch API for larger files."
        )

    url = f"{endpoint}/translator/document:translate"
    params = {"targetLanguage": target_language_iso_code, "api-version": SYNC_API_VERSION}
    if source_language and source_language.lower() != "auto":
        params["sourceLanguage"] = source_language

    headers = {"Ocp-Apim-Subscription-Key": key}
    if region:
        headers["Ocp-Apim-Subscription-Region"] = region

    dst = (
        Path(output_path)
        if output_path
        else src.with_stem(f"{src.stem}.{target_language_iso_code}")
    )

    ctype_doc = _guess_content_type(src)
    files = {}
    # open files within the retry loop to ensure clean handles on retries
    attempt = 0
    while True:
        with open(src, "rb") as df:
            files["document"] = (src.name, df, ctype_doc)
            if glossary_path:
                g = Path(glossary_path)
                if not g.is_file():
                    raise RuntimeError(f"Glossary file not found: {glossary_path}")
                ctype_gloss = _guess_content_type(g)
                gf = open(g, "rb")
                files["glossary"] = (g.name, gf, ctype_gloss)
            try:
                with requests.post(
                    url,
                    params=params,
                    headers=headers,
                    files=files,
                    stream=True,
                    timeout=timeout_s,
                ) as r:
                    # Close glossary handle early if present
                    if glossary_path:
                        files["glossary"][1].close()
                    if r.status_code == 200:
                        # stream to disk
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        with open(dst, "wb") as out:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    out.write(chunk)
                        return str(dst)
                    elif r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                        # simple retry with exponential backoff
                        retry_after = r.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            time.sleep(int(retry_after))
                        else:
                            _backoff_sleep(attempt)
                        attempt += 1
                        continue
                    else:
                        try:
                            err = r.text
                        except Exception:
                            err = "<no body>"
                        raise RuntimeError(f"Translator error {r.status_code}: {err}")
            finally:
                if glossary_path and not files["glossary"][1].closed:
                    files["glossary"][1].close()
        # loop end (on retry)
    # unreachable


@flock_type
class DocumentTranslator(BaseModel):
    name: str = Field(..., description="Name of the document")
    description: str = Field(..., description="Description of the document")
    input_language: str = Field(..., description="Input language of the document")
    output_language: str = Field(..., description="Output language of the document")
    input_pages: list[str] = Field(..., description="Input pages of the document")
    output_pages: list[str] = Field(..., description="The translated output pages of the document. Decided by the agent.")
    unsure_translations: list[str] = Field(..., description="The unsure translations of the document. Decided by the agent.")

# "groq/qwen-qwq-32b"    #"openai/gpt-4o" #

flock = Flock(model="openai/gpt-5")

translation_agent = FlockFactory.create_default_agent(
    name="translation_agent",
    description="An agent that translates a document from one language to another",
    input="path: str, output_language: str, output_dir: str",
    output="output_path: str",
    tools=[translate_document_sync],
    stream=True,
    temperature=1.0,
    max_tokens=120000,
)

flock.add_agent(translation_agent)

path = "data/SAP Joule EN.docx"
output_language = "Deutsch"
output_dir = "data_translated/"

#translate_document_sync(path, "de", output_dir + "test.pdf")

result = flock.run(
    agent=translation_agent,
    input={
        "path": path,
        "output_language": output_language,
        "output_dir": output_dir,
    },
)
print(result.output_path)



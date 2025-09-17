#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
from typing import Optional
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
import argparse
import mimetypes
import os
import sys
import time
import requests
from flock.core import Flock, FlockFactory, flock_type, flock_tool
from flock.core.logging.logging import get_logger as _get_logger
from flock.core.logging.logging import configure_logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.document import DocumentTranslationClient, TranslationGlossary
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions,
    BlobSasPermissions,
    generate_container_sas,
    generate_blob_sas,
)

log = _get_logger("pdf_translate")
configure_logging("DEBUG","DEBUG")

def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _new_container_name(prefix: str) -> str:
    # container name: 3–63 lowercase alphanum or hyphen; start/end alphanum
    return f"{prefix}-{uuid.uuid4().hex[:22]}"  # keeps <= 63 total with prefix


def _make_blob_clients():
    account = _require_env("AZURE_STORAGE_ACCOUNT_NAME")
    key = _require_env("AZURE_STORAGE_ACCOUNT_KEY")
    service = BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net", credential=key
    )
    return account, key, service


def _upload_blob(container_client, local_path: Path, blob_name: str) -> None:
    with open(local_path, "rb") as fh:
        container_client.upload_blob(name=blob_name, data=fh, overwrite=True)


def _container_sas(account: str, key: str, container: str, perms: ContainerSasPermissions, minutes=120):
    expiry = datetime.utcnow() + timedelta(minutes=minutes)
    return generate_container_sas(
        account_name=account,
        container_name=container,
        account_key=key,
        permission=perms,
        expiry=expiry,
    )


def _blob_sas(account: str, key: str, container: str, blob: str, perms: BlobSasPermissions, minutes=120):
    expiry = datetime.utcnow() + timedelta(minutes=minutes)
    return generate_blob_sas(
        account_name=account,
        container_name=container,
        blob_name=blob,
        account_key=key,
        permission=perms,
        expiry=expiry,
    )


def _glossary_format_from_ext(ext: str) -> str:
    # Strings align with get-supported-glossary-formats: CSV, TSV, XLIFF. :contentReference[oaicite:5]{index=5}
    e = ext.lower().lstrip(".")
    if e == "csv":
        return "CSV"
    if e in ("tsv", "tab"):
        return "TSV"
    if e in ("xlf", "xliff"):
        return "XLIFF"
    raise RuntimeError(f"Unsupported glossary extension: .{ext}")



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
        log.error(message=message)

    except Exception as e:
        # catch-all
        message = f"Tool: '_convert_pdf_to_markdown': Exception occured: {e} "
        log.error(message=message)

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
def extract_markdown(in_path: str, out_path: str) -> str:
    from markitdown import MarkItDown

    md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
    result = md.convert(in_path)
    print(result.text_content)
    with open(out_path, "w") as f:
        f.write(result.text_content)
    return result.text_content



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



@flock_tool
def translate_pdf_inplace(
    input_pdf: str,
    target_language: str,
    source_language: str | None = None,
    glossary_path: str | None = None,
    output_path: str | None = None,
    category_id: str | None = None,  # Custom Translator category (optional)
    sas_minutes: int = 120,
    poll_timeout_s: int = 3600,
) -> str:
    """
    Uploads a single PDF to a temporary source container, runs *batch* Document Translation,
    downloads the translated PDF to disk, and cleans up containers.

    Returns: local path of the translated PDF.
    """
    in_path = Path(input_pdf)
    if not in_path.is_file():
        raise RuntimeError(f"File not found: {input_pdf}")
    if in_path.suffix.lower() != ".pdf":
        raise RuntimeError("This function translates PDFs. Use the Office path for .docx/.pptx/.xlsx.")

    endpoint = _require_env("AZURE_TRANSLATOR_ENDPOINT").rstrip("/")
    key = _require_env("AZURE_TRANSLATOR_KEY")

    account, account_key, blob_service = _make_blob_clients()

    src_container = _new_container_name("trsrc")
    tgt_container = _new_container_name("trtgt")

    src_client = blob_service.create_container(src_container)
    tgt_client = blob_service.create_container(tgt_container)

    try:
        # 1) Upload the PDF
        blob_name = in_path.name
        log.info("Uploading source PDF %s to container %s", blob_name, src_container)
        _upload_blob(src_client, in_path, blob_name)

        # 2) (Optional) upload glossary and build its SAS URL
        glossary_url = None
        glossary_obj = None
        if glossary_path:
            gpath = Path(glossary_path)
            if not gpath.is_file():
                raise RuntimeError(f"Glossary not found: {glossary_path}")
            g_blob = gpath.name
            log.info("Uploading glossary %s", g_blob)
            _upload_blob(src_client, gpath, g_blob)
            g_sas = _blob_sas(
                account, account_key, src_container, g_blob, BlobSasPermissions(read=True), minutes=sas_minutes
            )
            glossary_url = f"https://{account}.blob.core.windows.net/{src_container}/{g_blob}?{g_sas}"
            glossary_format = _glossary_format_from_ext(gpath.suffix)
            glossary_obj = TranslationGlossary(glossary_url=glossary_url, file_format=glossary_format)

        # 3) Generate SAS URLs for source (read+list) and target (write+create+add+list)
        src_sas = _container_sas(
            account,
            account_key,
            src_container,
            ContainerSasPermissions(read=True, list=True),
            minutes=sas_minutes,
        )
        tgt_sas = _container_sas(
            account,
            account_key,
            tgt_container,
            ContainerSasPermissions(write=True, create=True, add=True, list=True),
            minutes=sas_minutes,
        )
        source_url = f"https://{account}.blob.core.windows.net/{src_container}?{src_sas}"
        target_url = f"https://{account}.blob.core.windows.net/{tgt_container}?{tgt_sas}"
        log.info("Source URL: %s", source_url)
        log.info("Target URL: %s", target_url)

        # 4) Start batch translation for exactly this blob (prefix filter)
        client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))
        log.info("Starting batch translation (PDF supported only in batch).")
        # Note: prefix limits to our single blob; glossary/category optional. :contentReference[oaicite:6]{index=6}
        poller = client.begin_translation(
            source_url,
            target_url,
            target_language,
            source_language=source_language,
            prefix=blob_name,  # restrict to this file name
            category_id=category_id,
            glossaries=[glossary_obj] if glossary_obj else None,
        )

        # 5) Wait for completion and check per-document status
        result_iter = poller.result(timeout=poll_timeout_s)
        succeeded = 0
        failed = 0
        for doc in result_iter:
            if str(doc.status).lower() == "succeeded":
                succeeded += 1
                log.info("Translated: %s -> %s", doc.source_document_url, doc.translated_to)
            else:
                failed += 1
                err = getattr(doc, "error", None)
                log.error("Failed: %s | %s", getattr(doc, "source_document_url", "?"), getattr(err, "message", ""))
        if succeeded == 0:
            raise RuntimeError("Translation did not produce any output; see logs above.")

        # 6) Download the translated PDF from the target container
        #    There can be a short delay before the blob is visible. :contentReference[oaicite:7]{index=7}
        out_path = Path(output_path) if output_path else in_path.with_stem(f"{in_path.stem}.{target_language}")
        out_path = out_path.with_suffix(".pdf")

        blob_to_download = None
        for attempt in range(20):
            blobs = list(tgt_client.list_blobs())
            if blobs:
                # Prefer exact name match; otherwise pick the first .pdf
                for b in blobs:
                    if Path(b.name).name == blob_name or b.name.lower().endswith(".pdf"):
                        blob_to_download = b.name
                        break
                if not blob_to_download:
                    blob_to_download = blobs[0].name
                break
            sleep(1.0)

        if not blob_to_download:
            raise RuntimeError("Translated blob not found in target container (eventual consistency delay?).")

        log.info("Downloading translated PDF: %s", blob_to_download)
        blob_client = tgt_client.get_blob_client(blob_to_download)
        data = blob_client.download_blob().readall()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)

        log.info("Saved: %s", out_path)
        return str(out_path)

    finally:
        # 7) Clean up ephemeral containers
        try:
            blob_service.delete_container(src_container)
        except Exception as e:
            log.warning("Failed to delete source container: %s", e)
        try:
            blob_service.delete_container(tgt_container)
        except Exception as e:
            log.warning("Failed to delete target container: %s", e)


def main():
    p = argparse.ArgumentParser(description="In-place PDF translation via Azure Document Translation (batch).")
    p.add_argument("--input", required=True, help="Path to a .pdf")
    p.add_argument("--to", required=True, help="Target language code (e.g., de, fr, ja)")
    p.add_argument("--source", default=None, help="Optional source language (omit for autodetect)")
    p.add_argument("--glossary", default=None, help="Optional glossary (CSV/TSV/XLIFF)")
    p.add_argument("--output", default=None, help="Optional path for the translated PDF")
    p.add_argument("--category", default=None, help="Optional Custom Translator category ID")
    p.add_argument("--timeout", type=int, default=3600, help="Poll timeout seconds (default 3600)")
    args = p.parse_args()

    try:
        out = translate_pdf_inplace(
            input_pdf=args.input,
            target_language=args.to,
            source_language=args.source,
            glossary_path=args.glossary,
            output_path=args.output,
            category_id=args.category,
            poll_timeout_s=args.timeout,
        )
        print(out)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        log.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    translate_pdf_inplace("/Users/ara/Projects/flock-showcase/05-full-projects/project-document-translator/data/JOBFIT Nova Introduction EN.pdf", "De")

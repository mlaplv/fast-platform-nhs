import logging
import os
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from lxml import html
import pymupdf

logger = logging.getLogger("knowledge-parser")


class KnowledgeParserService:
    def _resolve_file_path(self, stored_path: str) -> Optional[str]:
        """
        Resolve a DB-stored relative path (e.g. /uploads/2026/05/abc.pdf)
        to the real absolute path inside the container.
        """
        if os.path.exists(stored_path):
            return stored_path

        candidates = [
            os.path.join("/app/frontend/static", stored_path.lstrip("/")),
            os.path.join("/app", stored_path.lstrip("/")),
            os.path.join("frontend/static", stored_path.lstrip("/")),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                logger.info(f"[KnowledgeParser] Resolved: {stored_path} -> {candidate}")
                return candidate

        logger.error(f"[KnowledgeParser] File not found in any location: {stored_path}")
        return None

    def _extract_html_text(self, raw_content: bytes) -> str:
        """Parse raw HTML bytes and return clean text content."""
        tree = html.fromstring(raw_content)
        for bad in tree.xpath("//script | //style | //nav | //footer | //header"):
            bad.getparent().remove(bad)
        raw_text = tree.text_content()
        lines = (line.strip() for line in raw_text.splitlines())
        return "\n".join(line for line in lines if line)

    async def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract plain text from a local PDF file using pymupdf."""
        def _parse() -> Optional[str]:
            real_path = self._resolve_file_path(file_path)
            if not real_path:
                return None
            try:
                doc = pymupdf.open(real_path)
                page_count = doc.page_count
                text_parts: list[str] = []
                for i in range(page_count):
                    page_text = doc[i].get_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                doc.close()

                combined = "\n\n".join(text_parts).strip()
                if not combined:
                    logger.warning(
                        f"[KnowledgeParser] PDF '{file_path}' has {page_count} pages "
                        f"but ZERO text — likely a scanned/image-only PDF."
                    )
                    return (
                        f"[PDF đính kèm — {page_count} trang. "
                        f"Đây là PDF dạng ảnh quét (scanned), không có lớp text. "
                        f"Vui lòng nhập nội dung thủ công hoặc dùng PDF có text layer.]"
                    )
                logger.info(
                    f"[KnowledgeParser] Extracted {len(combined)} chars "
                    f"from {page_count} pages: {file_path}"
                )
                return combined
            except Exception as e:
                logger.error(f"[KnowledgeParser] pymupdf error on '{file_path}': {e}")
                return None

        return await asyncio.to_thread(_parse)

    async def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text from an uploaded HTML or TXT file.
        Production-safe: file is read from server storage after upload, no local paths.
        """
        def _parse() -> Optional[str]:
            real_path = self._resolve_file_path(file_path)
            if not real_path:
                return None
            try:
                ext = os.path.splitext(real_path)[1].lower()
                with open(real_path, "rb") as f:
                    raw_content = f.read()

                if ext in (".html", ".htm"):
                    text = self._extract_html_text(raw_content)
                else:
                    lines = (
                        line.strip()
                        for line in raw_content.decode("utf-8", errors="replace").splitlines()
                    )
                    text = "\n".join(line for line in lines if line)

                if not text:
                    logger.warning(f"[KnowledgeParser] File '{file_path}' returned empty text.")
                    return None

                logger.info(f"[KnowledgeParser] Extracted {len(text)} chars from file: {file_path}")
                return text
            except Exception as e:
                logger.error(f"[KnowledgeParser] Error reading file '{file_path}': {e}")
                return None

        return await asyncio.to_thread(_parse)

    async def extract_text_from_url(self, url: str) -> Optional[str]:
        """Crawl an HTTP/HTTPS URL and extract clean text content."""
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 Micsmo/Bot"})
                resp.raise_for_status()

            text = self._extract_html_text(resp.content)
            if not text:
                logger.warning(f"[KnowledgeParser] URL '{url}' returned empty text.")
                return None

            logger.info(f"[KnowledgeParser] Extracted {len(text)} chars from URL: {url}")
            return text

        except Exception as e:
            logger.error(f"[KnowledgeParser] Failed to crawl URL '{url}': {e}")
            return None

    async def _delete_source_file(self, file_path: str, db_session: AsyncSession) -> None:
        """
        Ultra-Lean cleanup: permanently delete the uploaded source file
        from both storage (disk) and MediaRegistry (DB) after extraction.
        """
        try:
            from backend.database.models import MediaRegistry
            from backend.services.storage.manager import storage
            from sqlalchemy import select

            stmt = select(MediaRegistry).where(MediaRegistry.file_path == file_path)
            res = await db_session.execute(stmt)
            media_asset = res.scalar_one_or_none()

            if media_asset:
                await storage.delete(file_path)
                await db_session.delete(media_asset)
                await db_session.commit()
                logger.info(f"[KnowledgeParser] ✅ Deleted from DB + Disk: {file_path}")
            else:
                real_path = self._resolve_file_path(file_path)
                if real_path and os.path.exists(real_path):
                    os.remove(real_path)
                    logger.info(f"[KnowledgeParser] ✅ Deleted orphan file from disk: {real_path}")
                else:
                    logger.warning(f"[KnowledgeParser] File not found for cleanup: {file_path}")

        except Exception as e:
            logger.error(f"[KnowledgeParser] Cleanup failed for '{file_path}': {e}")

    async def process_knowledge_source(self, knowledge_id: str) -> None:
        """
        Background task:
        1. Wait 2s for main request to commit source_url to DB.
        2. Dispatch extraction based on source_type (PDF | HTML | URL).
        3. Save extracted text to answer field + re-embed into Vector DB.
        4. Delete source file (PDF/HTML) — Ultra-Lean zero-persistence policy.
        """
        logger.info(
            f"[KnowledgeParser] 🚀 Task started for {knowledge_id}. "
            f"Waiting 2s for DB commit..."
        )
        await asyncio.sleep(2)

        try:
            from backend.database.models.system import SupportKnowledge
            from backend.services.commerce.knowledge_vector import knowledge_vector_service
            from backend.database.alchemy_config import alchemy_config
            from sqlalchemy import select

            async_sessionmaker = alchemy_config.create_session_maker()
            async with async_sessionmaker() as db_session:
                stmt = select(SupportKnowledge).where(SupportKnowledge.id == knowledge_id)
                res = await db_session.execute(stmt)
                item = res.scalar_one_or_none()

                if not item:
                    logger.warning(f"[KnowledgeParser] Item {knowledge_id} not found in DB.")
                    return

                if not item.source_url:
                    logger.warning(
                        f"[KnowledgeParser] Item {knowledge_id} has no source_url. Skipping."
                    )
                    return

                logger.info(
                    f"[KnowledgeParser] Processing: type={item.source_type}, "
                    f"url={item.source_url}"
                )

                extracted_text: Optional[str] = None
                if item.source_type == "PDF":
                    extracted_text = await self.extract_text_from_pdf(item.source_url)
                elif item.source_type == "URL":
                    extracted_text = await self.extract_text_from_url(item.source_url)
                elif item.source_type == "HTML":
                    extracted_text = await self.extract_text_from_file(item.source_url)

                if extracted_text:
                    item.answer = extracted_text[:15000]
                    await db_session.commit()
                    logger.info(
                        f"[KnowledgeParser] ✅ Answer saved "
                        f"({len(extracted_text)} chars) for {knowledge_id}"
                    )

                    await knowledge_vector_service.upsert_embedding(
                        db_session, knowledge_id, f"{item.question} {item.answer}"
                    )
                    logger.info(
                        f"[KnowledgeParser] ✅ Vector embedding updated for {knowledge_id}"
                    )

                    # Ultra-Lean: raw source files are single-use — purge immediately
                    if item.source_type in ("PDF", "HTML"):
                        await self._delete_source_file(item.source_url, db_session)
                else:
                    logger.error(
                        f"[KnowledgeParser] ❌ Extraction returned None for {knowledge_id}. "
                        f"Existing answer preserved."
                    )

        except Exception as e:
            logger.error(
                f"[KnowledgeParser] ❌ Crashed for {knowledge_id}: {e}",
                exc_info=True,
            )


knowledge_parser_service = KnowledgeParserService()

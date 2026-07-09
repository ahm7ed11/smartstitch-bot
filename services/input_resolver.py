"""
بيحول أي مصدر إدخال (ملف مرفوع / لينك ديسكورد zip / لينك جوجل درايف zip / لينك فولدر جوجل درايف)
لفولدر محلي فيه صور + اسم الفصل.
"""
import os

import aiohttp

from services import drive_service
from utils.zip_utils import safe_extract_zip, sanitize_name


class InputError(Exception):
    pass


async def _download_http(url: str, dest_path: str):
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise InputError(f"فشل تحميل الرابط، كود الحالة: {resp.status}")
            os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
            with open(dest_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    f.write(chunk)
    return dest_path


def _filename_from_url(url: str) -> str:
    from urllib.parse import unquote, urlparse

    path = urlparse(url).path
    name = os.path.basename(path)
    return unquote(name) or "chapter.zip"


async def resolve_from_attachment(attachment, work_dir: str) -> tuple[str, str]:
    """attachment: discord.Attachment (لازم يكون zip)"""
    filename = attachment.filename
    if not filename.lower().endswith(".zip"):
        raise InputError("الملف اللي رفعته لازم يكون ملف ZIP.")
    chapter_name = sanitize_name(os.path.splitext(filename)[0])
    zip_path = os.path.join(work_dir, "input.zip")
    os.makedirs(work_dir, exist_ok=True)
    await attachment.save(zip_path)
    input_dir = os.path.join(work_dir, "input_images")
    safe_extract_zip(zip_path, input_dir)
    return input_dir, chapter_name


async def resolve_from_link(link: str, work_dir: str) -> tuple[str, str]:
    link = link.strip()
    input_dir = os.path.join(work_dir, "input_images")
    os.makedirs(work_dir, exist_ok=True)

    if drive_service.is_drive_link(link):
        folder_id = drive_service.extract_folder_id(link)
        if folder_id:
            meta = await _to_thread(drive_service.get_metadata, folder_id)
            chapter_name = sanitize_name(meta.get("name", "chapter"))
            count = await _to_thread(
                drive_service.download_folder_recursive, folder_id, input_dir
            )
            if count == 0:
                raise InputError("الفولدر ده على درايف مفيهوش صور، أو الـ Service Account مالوش صلاحية وصول عليه.")
            return input_dir, chapter_name

        file_id = drive_service.extract_file_id(link)
        if file_id:
            meta = await _to_thread(drive_service.get_metadata, file_id)
            name = meta.get("name", "chapter.zip")
            mime = meta.get("mimeType", "")
            chapter_name = sanitize_name(os.path.splitext(name)[0])
            if not (name.lower().endswith(".zip") or mime == "application/zip"):
                raise InputError(
                    "لينك جوجل درايف ده مش لينك فولدر ولا ملف ZIP. ابعت لينك فولدر فيه صور أو لينك ملف ZIP."
                )
            zip_path = os.path.join(work_dir, "input.zip")
            await _to_thread(drive_service.download_file_bytes, file_id, zip_path)
            safe_extract_zip(zip_path, input_dir)
            return input_dir, chapter_name

        raise InputError("مقدرتش أفهم لينك جوجل درايف ده. تأكد إنه لينك فولدر أو لينك ملف ZIP صحيح ومشارك.")

    # رابط عادي (زي لينك ملف zip من ديسكورد)
    filename = _filename_from_url(link)
    if not filename.lower().endswith(".zip"):
        filename += ".zip"
    chapter_name = sanitize_name(os.path.splitext(filename)[0])
    zip_path = os.path.join(work_dir, "input.zip")
    await _download_http(link, zip_path)
    safe_extract_zip(zip_path, input_dir)
    return input_dir, chapter_name


async def _to_thread(func, *args):
    import asyncio

    return await asyncio.to_thread(func, *args)


async def resolve_input(work_dir: str, attachment=None, link: str | None = None) -> tuple[str, str]:
    if attachment is not None:
        return await resolve_from_attachment(attachment, work_dir)
    if link:
        return await resolve_from_link(link, work_dir)
    raise InputError("لازم تبعت إما ملف ZIP أو لينك (ديسكورد/جوجل درايف).")

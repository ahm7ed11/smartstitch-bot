import os
import re
import zipfile


def sanitize_name(name: str) -> str:
    """بتنضف اسم عشان يصلح كاسم فولدر/ملف"""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]+', '_', name)
    name = name.strip(' .')
    return name or "chapter"


def safe_extract_zip(zip_path: str, dest_dir: str) -> str:
    """
    بتفك الزيب بأمان (بتحمي من Zip Slip attack) وترجع مسار الفولدر اللي اتفكت فيه الصور.
    """
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            member_path = os.path.join(dest_dir, member.filename)
            abs_dest = os.path.abspath(dest_dir)
            abs_target = os.path.abspath(member_path)
            if not abs_target.startswith(abs_dest + os.sep) and abs_target != abs_dest:
                raise ValueError(f"Unsafe path detected in zip: {member.filename}")
        zf.extractall(dest_dir)
    return dest_dir


def zip_directory(src_dir: str, output_zip_path: str) -> str:
    """بتضغط فولدر كامل في ملف zip واحد."""
    if output_zip_path.endswith('.zip'):
        output_zip_path = output_zip_path[:-4]
    return shutil_make_archive(src_dir, output_zip_path)


def shutil_make_archive(src_dir: str, output_zip_path_no_ext: str) -> str:
    import shutil

    archive_path = shutil.make_archive(output_zip_path_no_ext, 'zip', src_dir)
    return archive_path

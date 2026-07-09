"""
بيلف على مكتبة SmartStitch الأصلية (core/) ويشغلها مع تقرير التقدم (progress).
"""
import gc
import os

from core.detectors import select_detector
from core.services import DirectoryExplorer, ImageHandler, ImageManipulator
from core.utils.constants import WIDTH_ENFORCEMENT


class StitchError(Exception):
    pass


def run_stitch(input_folder: str, settings: dict, progress_cb=None) -> str:
    """
    بتشغل عملية الدمج والتقطيع الكاملة.
    settings keys: output_type ('.jpg'), lossy_quality (95), split_height (12000),
                   custom_width (720), detection_type ('pixel'), detection_senstivity (90),
                   ignorable_pixels (5), scan_line_step (5)
    progress_cb(fraction: float 0..1, message: str)
    بترجع مسار الفولدر الرئيسي اللي فيه الناتج (output root).
    """

    def report(fraction, message):
        if progress_cb:
            progress_cb(min(max(fraction, 0.0), 1.0), message)

    explorer = DirectoryExplorer()
    img_handler = ImageHandler()
    img_manipulator = ImageManipulator()
    detector = select_detector(detection_type=settings.get("detection_type", "pixel"))
    custom_width = settings.get("custom_width", -1) or -1
    width_enforce_mode = (
        WIDTH_ENFORCEMENT.MANUAL if custom_width > 0 else WIDTH_ENFORCEMENT.NONE
    )

    report(0.0, "بيدور على الفولدرات اللي فيها صور...")
    try:
        input_dirs = explorer.run(input=input_folder)
    except Exception as e:
        raise StitchError(f"مفيش صور اتلاقت في الملف ده: {e}")

    total_dirs = len(input_dirs)
    if total_dirs == 0:
        raise StitchError("مفيش صور اتلاقت في الملف ده.")

    # كل directory بياخد 5 خطوات فرعية (تحميل - تصغير - دمج - تقطيع - حفظ)
    steps_per_dir = 5
    total_steps = total_dirs * steps_per_dir
    step_counter = 0

    output_root = None

    for dir_index, work_dir in enumerate(input_dirs, start=1):
        if output_root is None:
            # output_path لأول working directory بيدينا اسم الروت (فيه لاحقة [stitched])
            output_root = _find_output_root(work_dir.output_path, input_folder)

        prefix = f"[{dir_index}/{total_dirs}]"

        imgs = img_handler.load(work_dir)
        step_counter += 1
        report(step_counter / total_steps, f"{prefix} تحميل الصور للذاكرة...")

        imgs = img_manipulator.resize(imgs, width_enforce_mode, custom_width)
        step_counter += 1
        report(step_counter / total_steps, f"{prefix} تظبيط عرض الصور...")

        combined_img = img_manipulator.combine(imgs)
        step_counter += 1
        report(step_counter / total_steps, f"{prefix} دمج الصور في صورة واحدة...")

        slice_points = detector.run(
            combined_img,
            settings.get("split_height", 12000),
            sensitivity=settings.get("detection_senstivity", 90),
            ignorable_pixels=settings.get("ignorable_pixels", 5),
            scan_step=settings.get("scan_line_step", 5),
        )
        step_counter += 1
        report(step_counter / total_steps, f"{prefix} تحديد نقاط التقطيع الذكية...")

        sliced_imgs = img_manipulator.slice(combined_img, slice_points)

        img_iteration = 1
        total_slices = max(len(sliced_imgs), 1)
        for img in sliced_imgs:
            img_handler.save(
                work_dir,
                img,
                img_iteration,
                img_format="." + settings.get("output_type", "jpg").lstrip("."),
                quality=settings.get("lossy_quality", 95),
            )
            img_iteration += 1
            sub_fraction = (step_counter + img_iteration / total_slices) / total_steps
            report(sub_fraction, f"{prefix} حفظ الصور الناتجة ({img_iteration - 1}/{total_slices})...")
        step_counter += 1
        report(step_counter / total_steps, f"{prefix} تم الانتهاء من هذا الفولدر ✅")

        gc.collect()

    report(1.0, "خلصت عملية الدمج والتقطيع ✅")
    return output_root


def _find_output_root(first_output_path: str, input_folder: str) -> str:
    """
    بيرجع مسار فولدر الناتج الرئيسي (اللي بيتنشأ جنب فولدر الإدخال بلاحقة ' [stitched]').
    """
    from core.utils.constants import OUTPUT_SUFFIX

    abs_input = os.path.abspath(input_folder)
    return abs_input + OUTPUT_SUFFIX

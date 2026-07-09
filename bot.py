import asyncio
import os
import shutil
import traceback
import uuid

import discord
from discord import app_commands

import config
from services import drive_service, stitch_service
from services.input_resolver import InputError, resolve_input
from services.progress_view import COLOR_ERROR, COLOR_SUCCESS, ProgressReporter, make_embed
from services.stitch_service import StitchError

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    try:
        await tree.sync()
    except Exception:
        traceback.print_exc()
    print(f"✅ البوت شغال باسم: {client.user}")


class ResultView(discord.ui.View):
    def __init__(self, drive_url: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="📂 افتح الفصل على درايف",
                style=discord.ButtonStyle.link,
                url=drive_url,
            )
        )


@tree.command(name="stitch", description="يدمج ويقطع صور فصل مانجا/مانهوا ويرفعها جوجل درايف")
@app_commands.describe(
    file="ملف ZIP فيه صور الفصل (اختياري لو هتبعت لينك)",
    link="لينك ZIP من ديسكورد، أو لينك ملف ZIP على درايف، أو لينك فولدر درايف فيه صور",
    output_format="صيغة الصور الناتجة (افتراضي: jpg)",
    quality="جودة الضغط لو jpg/webp من 1 لـ100 (افتراضي: 95)",
    rough_height="الارتفاع التقريبي لكل صورة ناتجة بالبكسل (افتراضي: 12000)",
    custom_width="عرض ثابت للصور الناتجة بالبكسل (افتراضي: 720، حط 0 لتعطيله)",
)
@app_commands.choices(
    output_format=[
        app_commands.Choice(name="jpg", value="jpg"),
        app_commands.Choice(name="png", value="png"),
        app_commands.Choice(name="webp", value="webp"),
    ]
)
async def stitch(
    interaction: discord.Interaction,
    file: discord.Attachment | None = None,
    link: str | None = None,
    output_format: app_commands.Choice[str] | None = None,
    quality: app_commands.Range[int, 1, 100] | None = None,
    rough_height: app_commands.Range[int, 500, 30000] | None = None,
    custom_width: app_commands.Range[int, 0, 5000] | None = None,
):
    if file is None and not link:
        await interaction.response.send_message(
            "❌ لازم تبعت إما ملف ZIP أو لينك (ديسكورد/جوجل درايف).", ephemeral=True
        )
        return

    settings = {
        "output_type": (output_format.value if output_format else config.DEFAULT_OUTPUT_FORMAT),
        "lossy_quality": quality if quality is not None else config.DEFAULT_LOSSY_QUALITY,
        "split_height": rough_height if rough_height is not None else config.DEFAULT_SPLIT_HEIGHT,
        "custom_width": custom_width if custom_width is not None else config.DEFAULT_CUSTOM_WIDTH,
        "detection_type": config.DEFAULT_DETECTION_TYPE,
        "detection_senstivity": config.DEFAULT_SENSITIVITY,
        "ignorable_pixels": config.DEFAULT_IGNORABLE_PIXELS,
        "scan_line_step": config.DEFAULT_SCAN_LINE_STEP,
    }

    await interaction.response.send_message(
        embed=make_embed("SmartStitch", 0.0, "بيبدأ العملية...")
    )

    job_id = uuid.uuid4().hex[:10]
    job_dir = os.path.join(config.WORK_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    loop = asyncio.get_running_loop()
    reporter = ProgressReporter(interaction, loop, title="SmartStitch")

    try:
        # --- 1) تجهيز/تحميل الصور ---
        await reporter.update_async(0.02, "📥 بيحمّل ملفاتك...")
        input_dir, chapter_name = await resolve_input(job_dir, attachment=file, link=link)

        # --- 2) عملية الدمج والتقطيع ---
        def progress_cb(fraction, message):
            # 5% لأول تحميل + 65% للستيتش + 30% للرفع على درايف
            overall = 0.05 + fraction * 0.65
            reporter.report_sync(overall, f"🧩 {message}")

        output_root = await asyncio.to_thread(
            stitch_service.run_stitch, input_dir, settings, progress_cb
        )

        if not output_root or not os.path.exists(output_root):
            raise StitchError("العملية خلصت بس مفيش ناتج اتحفظ.")

        # --- 3) الرفع على جوجل درايف ---
        await reporter.update_async(0.72, "☁️ بيرفع الصور على جوجل درايف...")
        parent_id = config.GOOGLE_DRIVE_PARENT_FOLDER_ID or None

        def create_and_upload():
            drive_folder_id = drive_service.create_folder(chapter_name, parent_id)

            def upload_progress(done, total):
                fraction = 0.72 + (done / max(total, 1)) * 0.25
                reporter.report_sync(fraction, f"☁️ بيرفع الصور... ({done}/{total})")

            drive_service.upload_directory(output_root, drive_folder_id, progress_cb=upload_progress)
            drive_service.make_public_readable(drive_folder_id)
            return drive_folder_id

        drive_folder_id = await asyncio.to_thread(create_and_upload)
        drive_url = drive_service.folder_link(drive_folder_id)

        image_count = sum(len(files) for _, _, files in os.walk(output_root))

        embed = make_embed(
            "SmartStitch",
            1.0,
            f"✅ تم بنجاح!\n**الفصل:** {chapter_name}\n**عدد الصور الناتجة:** {image_count}",
            color=COLOR_SUCCESS,
            footer="SmartStitch Bot",
        )
        await interaction.edit_original_response(embed=embed, view=ResultView(drive_url))

    except (InputError, StitchError, drive_service.DriveError) as e:
        embed = make_embed("SmartStitch", 1.0, f"❌ حصل خطأ:\n{e}", color=COLOR_ERROR)
        await interaction.edit_original_response(embed=embed, view=None)
    except Exception as e:
        traceback.print_exc()
        embed = make_embed(
            "SmartStitch", 1.0, f"❌ حصل خطأ غير متوقع:\n`{e}`", color=COLOR_ERROR
        )
        await interaction.edit_original_response(embed=embed, view=None)
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)


if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        raise SystemExit("❌ لازم تحط DISCORD_TOKEN في ملف .env")
    client.run(config.DISCORD_TOKEN)

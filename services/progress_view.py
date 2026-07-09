import time

import discord

BAR_LENGTH = 20
FILLED = "█"
EMPTY = "░"

COLOR_RUNNING = 0x5865F2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245


def make_bar(fraction: float) -> str:
    fraction = max(0.0, min(1.0, fraction))
    filled = round(fraction * BAR_LENGTH)
    return FILLED * filled + EMPTY * (BAR_LENGTH - filled)


def make_embed(title: str, fraction: float, status_text: str, color=COLOR_RUNNING, footer: str | None = None) -> discord.Embed:
    percent = round(fraction * 100)
    embed = discord.Embed(
        title=title,
        description=f"`{make_bar(fraction)}`  **{percent}%**\n\n{status_text}",
        color=color,
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


class ProgressReporter:
    """
    بيدير تحديث رسالة الديسكورد بالـ progress bar من غير ما يعمل spam على الـ API
    (بيحدث كل ثانية على الأكتر كحد أقصى).
    """

    def __init__(self, interaction: discord.Interaction, loop, title: str, min_interval: float = 1.2):
        self.interaction = interaction
        self.loop = loop
        self.title = title
        self.min_interval = min_interval
        self._last_update = 0.0
        self._last_fraction = -1.0

    def report_sync(self, fraction: float, message: str):
        """بينادى من أي thread تاني (مش الـ event loop)."""
        now = time.time()
        should_update = (
            fraction >= 1.0
            or now - self._last_update >= self.min_interval
            or fraction - self._last_fraction >= 0.03
        )
        if not should_update:
            return
        self._last_update = now
        self._last_fraction = fraction
        import asyncio

        try:
            asyncio.run_coroutine_threadsafe(self._update(fraction, message), self.loop)
        except RuntimeError:
            pass

    async def _update(self, fraction: float, message: str):
        embed = make_embed(self.title, fraction, message)
        try:
            await self.interaction.edit_original_response(embed=embed)
        except discord.HTTPException:
            pass

    async def update_async(self, fraction: float, message: str, color=COLOR_RUNNING, footer=None):
        embed = make_embed(self.title, fraction, message, color=color, footer=footer)
        try:
            await self.interaction.edit_original_response(embed=embed)
        except discord.HTTPException:
            pass

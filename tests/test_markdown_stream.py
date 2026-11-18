"""Tests for the pacing of `MarkdownStream`."""

from __future__ import annotations

import asyncio
import time

from textual.app import App, ComposeResult
from textual.widgets import Markdown


class StreamApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Markdown()


FRAGMENTS = [f"Line {n} of the streamed text.\n\n" for n in range(40)]


async def test_stream_text_is_unchanged() -> None:
    """Fragments written in quick succession all arrive, in order."""
    async with StreamApp().run_test() as pilot:
        markdown = pilot.app.query_one(Markdown)
        stream = Markdown.get_stream(markdown)
        for fragment in FRAGMENTS:
            await stream.write(fragment)
        await stream.stop()
        await pilot.pause()
        assert markdown.source == "".join(FRAGMENTS)


async def test_stream_rests_between_appends(monkeypatch) -> None:
    """The stream leaves idle time after a slow append, so other work can run.

    Each (slowed) append is followed by a rest of at least the time the append took, and
    fragments written meanwhile are joined into fewer appends.

    Regression test for https://github.com/Textualize/textual/issues/<number>
    """
    spans: list[tuple[float, float]] = []

    async with StreamApp().run_test() as pilot:
        markdown = pilot.app.query_one(Markdown)
        original_append = markdown.append

        def slow_append(fragment: str):
            async def run() -> None:
                start = time.monotonic()
                await asyncio.sleep(0.05)
                await original_append(fragment)
                spans.append((start, time.monotonic()))

            return run()

        monkeypatch.setattr(markdown, "append", slow_append)
        stream = Markdown.get_stream(markdown)
        for fragment in FRAGMENTS:
            await stream.write(fragment)
            await asyncio.sleep(0.005)
        await stream.stop()
        await pilot.pause()

        assert markdown.source == "".join(FRAGMENTS)

    assert 1 < len(spans) < len(FRAGMENTS)
    for (_, end), (next_start, _) in zip(spans, spans[1:]):
        assert next_start - end >= 0.05

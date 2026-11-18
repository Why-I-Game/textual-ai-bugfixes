from textual.app import App, ComposeResult
from textual.widgets import TextArea


async def test_cursor_visible_when_typing_wraps_a_scrolled_text_area():
    """Typing that wraps onto a new visual line must scroll the cursor into view.

    Regression test for https://github.com/Textualize/textual/issues/<number>
    """

    class WrapApp(App):
        CSS = "TextArea { height: 8; border: none; padding: 0; }"

        def compose(self) -> ComposeResult:
            yield TextArea(soft_wrap=True)

    app = WrapApp()
    async with app.run_test(size=(40, 20)) as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("word " * 60)
        text_area.move_cursor(text_area.document.end)
        await pilot.pause()
        wraps = 0
        for _ in range(40):
            rows = text_area.wrapped_document.height
            await pilot.press("x")
            if text_area.wrapped_document.height != rows:
                wraps += 1
            row = text_area.cursor_screen_offset.y - text_area.region.y
            assert 0 <= row < text_area.size.height
        assert wraps >= 1

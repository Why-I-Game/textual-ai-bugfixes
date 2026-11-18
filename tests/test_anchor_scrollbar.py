from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static


class AnchoredApp(App):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            for n in range(100):
                yield Static(f"Line {n}")

    def on_mount(self) -> None:
        self.query_one(VerticalScroll).anchor()


def scrollbar_column(app: App) -> list:
    """The segments of the last screen column (the vertical scrollbar)."""
    return [
        list(strip.crop(strip.cell_length - 1, strip.cell_length))
        for strip in app.screen._compositor.render_strips()
    ]


async def test_anchored_scrollbar_repainted_after_resize():
    """An anchored container scrolled to its new bottom by a resize must repaint its
    scrollbar, or the thumb stays where it was drawn at the old size.

    Regression test for https://github.com/Textualize/textual/issues/<number>
    """
    resized_app = AnchoredApp()
    async with resized_app.run_test(size=(40, 30)) as pilot:
        await pilot.pause()
        await pilot.resize_terminal(40, 15)
        await pilot.pause()
        resized = scrollbar_column(resized_app)

    fresh_app = AnchoredApp()
    async with fresh_app.run_test(size=(40, 15)) as pilot:
        await pilot.pause()
        fresh = scrollbar_column(fresh_app)

    assert resized == fresh

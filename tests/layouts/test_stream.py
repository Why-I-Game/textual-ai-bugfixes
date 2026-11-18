from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static


async def test_stream_layout_height_respects_horizontal_margin():
    """A widget with a horizontal margin in a stream layout must be measured at the
    width it is placed with, or wrapped text loses its last line.

    Regression test for https://github.com/Textualize/textual/issues/6794
    """

    class StreamMarginApp(App):
        CSS = """
        VerticalScroll { layout: stream; scrollbar-size-vertical: 0; }
        Static { margin: 0 1; }
        """

        def compose(self) -> ComposeResult:
            with VerticalScroll():
                # 40 cells: one line at width 40, two lines at width 38.
                yield Static("x" * 36 + " end", id="wrapped")

    app = StreamMarginApp()
    async with app.run_test(size=(40, 10)):
        static = app.query_one("#wrapped", Static)
        assert static.region.width == 38
        assert static.region.height == 2

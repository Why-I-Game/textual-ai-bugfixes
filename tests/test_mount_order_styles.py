from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.dom import DOMNode
from textual.widgets import Label, Static


class SubStatic(Static):
    pass


class OrderApp(App):
    CSS = """
    Static { margin: 0; padding: 0; text-align: left; }
    Static:last-child { margin: 0 0 1 0; }
    Static:last-of-type { padding: 1 0 0 0; }
    Label:last-of-type { text-align: right; }
    """

    def compose(self) -> ComposeResult:
        yield Vertical()


def order_styles(container: Vertical) -> list[tuple[int, int, str]]:
    return [
        (
            child.styles.margin.bottom,
            child.styles.padding.top,
            child.styles.text_align,
        )
        for child in container.children
    ]


def expected(widgets: list) -> list[tuple[int, int, str]]:
    """The styles the CSS above gives, worked out from the final order."""
    result = []
    for index, widget in enumerate(widgets):
        later = widgets[index + 1 :]
        last_child = index == len(widgets) - 1
        last_of_type = not any(isinstance(other, type(widget)) for other in later)
        result.append(
            (
                1 if last_child else 0,
                1 if last_of_type else 0,
                "right" if isinstance(widget, Label) and last_of_type else "left",
            )
        )
    return result


async def test_mount_at_end_updates_last_child_and_last_of_type():
    """Appending widgets must restyle the old last child and the old last of each
    type (subclasses included).

    Regression test for https://github.com/Textualize/textual/issues/<number>
    """
    app = OrderApp()
    async with app.run_test() as pilot:
        container = app.query_one(Vertical)
        order = [
            [Static("a")],
            [Static("b"), SubStatic("c")],
            [Label("d")],
            [SubStatic("e")],
            [Static("f"), Label("g")],
            [Static("h")],
            [Label("i")],
        ]
        mounted: list = []
        for widgets in order:
            await container.mount(*widgets)
            await pilot.pause()
            mounted.extend(widgets)
            assert order_styles(container) == expected(mounted)


async def test_mount_at_end_does_not_restyle_every_sibling():
    """Appending one widget restyles a bounded number of widgets, not every sibling.

    Regression test for https://github.com/Textualize/textual/issues/<number>
    """
    calls = 0
    original = DOMNode.update_node_styles

    def counting(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        return original(self, *args, **kwargs)

    app = OrderApp()
    async with app.run_test() as pilot:
        container = app.query_one(Vertical)
        await container.mount_all([Static(str(n)) for n in range(100)])
        await pilot.pause()
        DOMNode.update_node_styles = counting
        try:
            await container.mount(Static("new"))
            await pilot.pause()
        finally:
            DOMNode.update_node_styles = original
        assert calls <= 5
        assert order_styles(container)[-2:] == [(0, 0, "left"), (1, 1, "left")]

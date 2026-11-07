from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from labelle.cli import cli


@pytest.fixture
def bitmap_output(monkeypatch):
    font = Path(cli.__file__).parents[1] / "resources/fonts/Carlito-Regular.ttf"
    monkeypatch.setattr(cli, "get_font_path", lambda **kwargs: font)
    monkeypatch.setattr(
        cli, "get_device_manager", Mock(side_effect=AssertionError("No hardware"))
    )
    output = Mock()
    monkeypatch.setattr(cli, "output_bitmap", output)
    return output


def render_barcode(bitmap_output, option, scale=None):
    args = ["--output", "console", "--tape-size-mm", "12", option, "Barcode"]
    if scale is not None:
        args.extend(["--font-scale", str(scale)])
    result = CliRunner().invoke(cli.app, args)
    assert result.exit_code == 0, (result.output, result.exception)
    return bitmap_output.call_args.args[0]


@pytest.mark.parametrize(
    ("scale", "ratio"), [(None, 0.9), (20, 0.2), (90, 0.9), (20.9, 0.2)]
)
def test_barcode_caption_receives_font_scale(bitmap_output, scale, ratio):
    with patch.object(
        cli, "BarcodeWithTextRenderEngine", wraps=cli.BarcodeWithTextRenderEngine
    ) as renderer:
        render_barcode(bitmap_output, "--barcode-with-text", scale)
    assert renderer.call_args.kwargs["font_size_ratio"] == ratio


@pytest.mark.parametrize("option", ["--barcode-with-text", "--barcode"])
def test_barcode_font_scale_bitmaps(bitmap_output, option):
    small = render_barcode(bitmap_output, option, 20)
    large = render_barcode(bitmap_output, option, 90)
    default = render_barcode(bitmap_output, option)

    assert small.size == large.size == default.size
    assert default.tobytes() == large.tobytes()
    if option == "--barcode-with-text":
        assert small.tobytes() != large.tobytes()
    else:
        assert small.tobytes() == large.tobytes()

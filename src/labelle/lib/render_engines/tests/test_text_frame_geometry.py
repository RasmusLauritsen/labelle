from pathlib import Path

import pytest
from PIL import ImageDraw, ImageFont

from labelle.lib.render_engines import RenderContext, TextRenderEngine

FONT_FILE_NAME = Path("src/labelle/resources/fonts/Carlito-Regular.ttf")


@pytest.mark.parametrize("frame_width_px", [30, 99])
@pytest.mark.parametrize(
    "text,height_px,font_size_ratio",
    [
        ("Hi", 64, 0.9),
        ("i", 100, 1.0),
        ("Wide text", 10, 1.0),
        ("Wide text", 9, 1.0),
        ("Wide text", 8, 1.0),
        ("Wide text", 7, 1.0),
        ("i", 1, 1.0),
        ("", 10, 1.0),
    ],
)
def test_oversized_frame_fits_image(frame_width_px, text, height_px, font_size_ratio):
    context = RenderContext(height_px=height_px)
    image = TextRenderEngine(
        text,
        FONT_FILE_NAME,
        frame_width_px=frame_width_px,
        font_size_ratio=font_size_ratio,
    ).render(context)
    unframed = TextRenderEngine(
        text, FONT_FILE_NAME, font_size_ratio=font_size_ratio
    ).render(context)
    assert image.size == unframed.size
    assert image.mode == unframed.mode

    expected = unframed.copy()
    width = min(frame_width_px, (image.width - 1) // 2, (height_px - 8) // 2)
    if width > 0:
        # Add only the border to the already-rendered text, independently of the
        # renderer's outer-fill/inner-clear implementation.
        draw = ImageDraw.Draw(expected)
        draw.rectangle((0, 4, image.width - 1, height_px - 4), outline=1, width=width)
    assert image.tobytes() == expected.tobytes()


@pytest.mark.parametrize("frame_width_px", [0, 1, 3, 5, 10])
def test_normal_frame_preserves_existing_pixels(frame_width_px):
    """Compare exactly with the original valid rectangle and text geometry."""
    context = RenderContext(height_px=100)
    text = "Hello, World!"
    image = TextRenderEngine(
        text, FONT_FILE_NAME, frame_width_px=frame_width_px
    ).render(context)
    expected = TextRenderEngine(text, FONT_FILE_NAME).render(context)
    draw = ImageDraw.Draw(expected)
    if frame_width_px:
        draw.rectangle((0, 4, image.width - 1, 96), fill=1)
        draw.rectangle(
            (
                frame_width_px,
                4 + frame_width_px,
                image.width - frame_width_px - 1,
                96 - frame_width_px,
            ),
            fill=0,
        )
        draw.multiline_text(
            (image.width / 2, 50),
            text,
            align="center",
            anchor="mm",
            font=ImageFont.truetype(str(FONT_FILE_NAME), 90),
            fill=1,
        )
    assert image.tobytes() == expected.tobytes()

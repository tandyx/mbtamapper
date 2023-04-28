from PIL import ImageDraw


def center_text(img, font, text, color="#ffffff", offset=(0, 0)):
    """centers text on image"""

    if text and text == text:
        text = str(int(text)).zfill(3)
        draw = ImageDraw.Draw(img)
        text_width, text_height = draw.textsize(text, font)
        position = (
            (img.width - text_width) / 2 + offset[0],
            (img.height - text_height) / 2 + offset[1],
        )
        draw.text(position, text, color, font=font)
        return img

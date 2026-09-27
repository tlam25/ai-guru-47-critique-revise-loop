"""Render captured terminal logs as 300 DPI PNG images."""

from pathlib import Path
import subprocess
import textwrap
import unicodedata

from PIL import Image, ImageDraw, ImageFont


FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf"


def wrap_line(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    if len(text) <= width:
        return [text]
    indent_size = min(len(text) - len(text.lstrip(" ")), 8)
    return textwrap.wrap(
        text,
        width=width,
        subsequent_indent=" " * indent_size,
        replace_whitespace=False,
        drop_whitespace=True,
        break_long_words=False,
        break_on_hyphens=False,
    )


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    shown = " ".join(command)
    output = unicodedata.normalize("NFC", completed.stdout.rstrip())
    return f"$ {shown}\n{output}"


def render(content: str, output_path: Path, title: str) -> None:
    content = unicodedata.normalize("NFC", content)
    lines: list[str] = []
    for line in content.splitlines():
        lines.extend(wrap_line(line, 93))

    font = ImageFont.truetype(FONT_PATH, 25)
    bold = ImageFont.truetype(FONT_BOLD_PATH, 24)
    width = 1800
    line_height = 38
    chrome_height = 82
    padding = 44
    height = chrome_height + padding * 2 + line_height * len(lines)
    image = Image.new("RGB", (width, height), "#101419")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, chrome_height), fill="#20262e")
    for x, color in ((35, "#ff5f57"), (75, "#febc2e"), (115, "#28c840")):
        draw.ellipse((x - 12, 29, x + 12, 53), fill=color)
    draw.text((width // 2, 41), title, font=bold, fill="#e6edf3", anchor="mm")

    y = chrome_height + padding
    for line in lines:
        color = "#7ee787" if line.startswith("$") else "#d6deeb"
        if "FAIL" in line or "Lỗi" in line:
            color = "#ff7b72"
        elif "PASS" in line or line.startswith("OK"):
            color = "#7ee787"
        draw.text((padding, y), line, font=font, fill=color)
        y += line_height

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, dpi=(300, 300), optimize=True)


def main() -> None:
    render(
        run(["python3", "demo/critique_revise.py", "--scenario", "early-stop"]),
        Path("fig/terminal-early-stop.png"),
        "critique-revise - demo",
    )
    render(
        run(["python3", "demo/critique_revise.py", "--scenario", "two-rounds"]),
        Path("fig/terminal-two-rounds.png"),
        "critique-revise - two rounds",
    )
    render(
        run(["python3", "-m", "unittest", "-v", "demo/test_loop.py"]),
        Path("fig/terminal-tests.png"),
        "python unittest",
    )


if __name__ == "__main__":
    main()
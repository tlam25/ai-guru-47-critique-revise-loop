"""Render captured terminal logs as 300 DPI PNG images."""

from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont


FONT_PATH = "/usr/local/texlive/2025/texmf-dist/fonts/truetype/public/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/local/texlive/2025/texmf-dist/fonts/truetype/public/dejavu/DejaVuSansMono-Bold.ttf"


def wrap_line(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + width] for index in range(0, len(text), width)]


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
    return f"$ {shown}\n{completed.stdout.rstrip()}"


def render(content: str, output_path: Path, title: str) -> None:
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
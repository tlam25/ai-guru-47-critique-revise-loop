"""Writer - Critic - Writer loop with at most two revision rounds."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Protocol


CHECKLIST = (
    "Rõ ràng: câu chữ dễ hiểu, mỗi đoạn có một ý chính.",
    "Đủ ý: có vấn đề, giải pháp, ví dụ và lời kêu gọi hành động.",
    "Đúng độ dài: nằm trong khoảng từ 90 đến 130 từ.",
)


@dataclass(frozen=True)
class Criterion:
    name: str
    passed: bool
    comment: str


@dataclass(frozen=True)
class Critique:
    criteria: tuple[Criterion, ...]
    summary: str

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.criteria)


@dataclass(frozen=True)
class LoopResult:
    initial_version: str
    critiques: tuple[Critique, ...]
    final_version: str
    revision_count: int


class Provider(Protocol):
    def write_initial(self, topic: str) -> str: ...

    def critique(self, draft: str, round_number: int) -> Critique: ...

    def revise(self, draft: str, critique: Critique, round_number: int) -> str: ...


class DemoProvider:
    """Deterministic provider for learning, screenshots and automated tests."""

    def __init__(self, scenario: str = "early-stop") -> None:
        self.scenario = scenario

    def write_initial(self, topic: str) -> str:
        return (
            "Nhiều nhóm muốn dùng AI để viết nội dung nhanh. Công cụ có thể tạo "
            "bản nháp trong vài giây và giúp người viết tiết kiệm thời gian. "
            "Bạn chỉ cần nhập chủ đề, sau đó nhận kết quả và đăng bài."
        )

    def critique(self, draft: str, round_number: int) -> Critique:
        word_count = len(draft.split())
        if round_number == 1:
            items = (
                Criterion("Rõ ràng", True, "Câu ngắn và dễ đọc."),
                Criterion(
                    "Đủ ý",
                    False,
                    "Thiếu rủi ro, bước kiểm tra và ví dụ cụ thể.",
                ),
                Criterion(
                    "Đúng độ dài",
                    90 <= word_count <= 130,
                    f"Bản nháp có {word_count} từ; yêu cầu 90-130 từ.",
                ),
            )
            return Critique(items, "Cần bổ sung nội dung và điều chỉnh độ dài.")

        clarity_passed = self.scenario != "two-rounds"
        items = (
            Criterion(
                "Rõ ràng",
                clarity_passed,
                "Luồng ý mạch lạc." if clarity_passed else "Đoạn giữa còn dồn nhiều ý.",
            ),
            Criterion("Đủ ý", True, "Đã có vấn đề, giải pháp, ví dụ và hành động."),
            Criterion("Đúng độ dài", True, "Nằm trong khoảng 90-130 từ."),
        )
        summary = "Đạt toàn bộ checklist." if clarity_passed else "Cần tách câu dài."
        return Critique(items, summary)

    def revise(self, draft: str, critique: Critique, round_number: int) -> str:
        if round_number == 1 and self.scenario == "two-rounds":
            return (
                "AI giúp nhóm nội dung tạo bản nháp nhanh, nhưng bản nháp đầu tiên có "
                "thể thiếu dữ kiện, lệch giọng hoặc dài hơn yêu cầu, vì vậy nhóm nên "
                "dùng một checklist cố định gồm rõ ràng, đủ ý và đúng độ dài để một "
                "vai Critic chỉ ra lỗi trước khi vai Writer sửa lại, chẳng hạn với bài "
                "giới thiệu workshop, Critic cần kiểm tra người đọc đã thấy lợi ích, "
                "thời gian tham gia, đối tượng phù hợp và lời đăng ký hay chưa; cách "
                "làm này biến việc góp ý thành bước có tiêu chí thay vì nhận xét cảm "
                "tính và giúp cả nhóm dễ lặp lại quy trình trong những lần viết sau."
            )
        return (
            "AI có thể giúp nhóm nội dung tạo bản nháp nhanh, nhưng kết quả đầu tiên "
            "thường chưa sẵn sàng để đăng. Bản nháp có thể thiếu dữ kiện, lệch giọng "
            "hoặc dài hơn yêu cầu. Vì vậy, bạn nên dùng một checklist cố định gồm rõ "
            "ràng, đủ ý và đúng độ dài. Ví dụ, với bài giới thiệu workshop, Critic "
            "kiểm tra xem người đọc đã biết lợi ích, thời gian, đối tượng phù hợp và "
            "cách đăng ký hay chưa. Writer chỉ sửa các điểm được nêu, rồi kiểm tra lại "
            "toàn bài. Vòng lặp ngắn này giúp phản hồi bớt cảm tính, giữ chi phí trong "
            "tầm kiểm soát và tạo ra phiên bản cuối dễ đọc hơn. Hãy bắt đầu với một "
            "bài ngắn trước khi áp dụng cho quy trình lớn."
        )


class OpenAIProvider:
    """Minimal Responses API adapter implemented with Python's standard library."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("Thiếu biến môi trường OPENAI_API_KEY.")

    def _request(self, instructions: str, user_input: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "instructions": instructions,
                "input": user_input,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API trả về HTTP {exc.code}: {body}") from exc
        texts = [
            part["text"]
            for item in data.get("output", [])
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        ]
        if not texts:
            raise RuntimeError("Không tìm thấy output_text trong phản hồi API.")
        return "\n".join(texts).strip()

    def write_initial(self, topic: str) -> str:
        return self._request(
            "Bạn là Writer. Viết tiếng Việt tự nhiên cho người mới.",
            f"Viết bài 90-130 từ về: {topic}",
        )

    def critique(self, draft: str, round_number: int) -> Critique:
        prompt = f"""
Đánh giá bản nháp theo đúng ba tiêu chí sau:
{chr(10).join(f'- {item}' for item in CHECKLIST)}

Chỉ trả JSON hợp lệ theo mẫu:
{{"criteria":[{{"name":"Rõ ràng","passed":true,"comment":"..."}},
{{"name":"Đủ ý","passed":false,"comment":"..."}},
{{"name":"Đúng độ dài","passed":true,"comment":"..."}}],
"summary":"..."}}

Bản nháp:
{draft}
""".strip()
        raw = self._request(
            "Bạn là Critic nghiêm khắc, cụ thể, không viết lại bài.",
            prompt,
        )
        parsed = json.loads(raw)
        criteria = tuple(Criterion(**item) for item in parsed["criteria"])
        return Critique(criteria, parsed["summary"])

    def revise(self, draft: str, critique: Critique, round_number: int) -> str:
        comments = "\n".join(
            f"- {item.name}: {item.comment}" for item in critique.criteria
        )
        return self._request(
            "Bạn là Writer. Chỉ xuất phiên bản bài viết đã sửa.",
            f"Sửa bản nháp theo phản hồi, giữ 90-130 từ.\n\n"
            f"Bản nháp:\n{draft}\n\nPhản hồi:\n{comments}",
        )


def run_loop(provider: Provider, topic: str, max_rounds: int = 2) -> LoopResult:
    if not 0 <= max_rounds <= 2:
        raise ValueError("max_rounds phải nằm trong khoảng 0-2.")

    draft = provider.write_initial(topic)
    initial = draft
    critiques: list[Critique] = []
    revision_count = 0

    for round_number in range(1, max_rounds + 1):
        critique = provider.critique(draft, round_number)
        critiques.append(critique)
        if critique.passed:
            break
        draft = provider.revise(draft, critique, round_number)
        revision_count += 1

    return LoopResult(initial, tuple(critiques), draft, revision_count)


def print_result(result: LoopResult) -> None:
    print("=== PHIÊN BẢN ĐẦU ===")
    print(result.initial_version)
    for index, critique in enumerate(result.critiques, start=1):
        print(f"\n=== NHẬN XÉT VÒNG {index} ===")
        for item in critique.criteria:
            marker = "PASS" if item.passed else "FAIL"
            print(f"[{marker}] {item.name}: {item.comment}")
        print(f"Tóm tắt: {critique.summary}")
    print("\n=== PHIÊN BẢN CUỐI ===")
    print(result.final_version)
    print(f"\nSố lần sửa: {result.revision_count}/2")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("demo", "live"), default="demo", help="Nguồn sinh văn bản."
    )
    parser.add_argument(
        "--scenario",
        choices=("early-stop", "two-rounds"),
        default="early-stop",
        help="Kịch bản dành cho chế độ demo.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
        help="Model dùng cho chế độ live.",
    )
    parser.add_argument(
        "--topic",
        default="Vì sao nhóm nội dung nên kiểm tra bản nháp do AI tạo",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        provider: Provider
        if args.mode == "live":
            provider = OpenAIProvider(args.model)
        else:
            provider = DemoProvider(args.scenario)
        print_result(run_loop(provider, args.topic))
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
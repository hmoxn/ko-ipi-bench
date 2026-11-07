"""시드 데이터(문서 x 인젝션)를 조합해 평가용 테스트 케이스를 생성합니다.

조합 축:
  문서(context) x 인젝션(injection) x 삽입 위치(position) x 난독화(obfuscation)

사용법:
  python -m kipi.build --seed-dir data/seed --out data/build/cases.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path

from . import obfuscate

POSITIONS = ("start", "middle", "end")


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def make_canary(case_id: str) -> tuple[str, str]:
    """케이스마다 고유한 카나리를 두 조각으로 만듭니다. 예: ('KIPI', '7F3A9C')"""
    digest = hashlib.sha256(case_id.encode()).hexdigest().upper()
    return "KIPI", digest[:6]


def insert_at(paragraphs: list[str], injection: str, position: str) -> list[str]:
    paras = list(paragraphs)
    if position == "start":
        idx = 0
    elif position == "middle":
        idx = len(paras) // 2
    elif position == "end":
        idx = len(paras)
    else:
        raise ValueError(position)
    paras.insert(idx, injection)
    return paras


def build_cases(contexts, injections, obfuscations, seed: int = 42) -> list[dict]:
    cases = []
    for ctx, inj, pos, obf in itertools.product(
        contexts, injections, POSITIONS, obfuscations
    ):
        case_id = f"{ctx['id']}__{inj['id']}__{pos}__{obf}"
        rng = random.Random(f"{seed}:{case_id}")  # 케이스별로 결정적인 난수
        a, b = make_canary(case_id)

        raw = inj["template"].replace("{A}", a).replace("{B}", b)
        injected_text = obfuscate.apply(obf, raw, rng, protect=(a, b))

        cases.append(
            {
                "id": case_id,
                "context_id": ctx["id"],
                "context_type": ctx["type"],
                "injection_id": inj["id"],
                "goal": inj["goal"],
                "register": inj["register"],
                "position": pos,
                "obfuscation": obf,
                "canary": a + b,  # 채점용 (결합된 형태)
                "user_task": ctx["user_task"],
                "document": "\n".join(insert_at(ctx["paragraphs"], injected_text, pos)),
            }
        )
    return cases


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed-dir", default="data/seed")
    p.add_argument("--out", default="data/build/cases.jsonl")
    p.add_argument(
        "--obfuscations",
        default=",".join(obfuscate.OBFUSCATIONS),
        help="쉼표로 구분 (기본: 전부)",
    )
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    seed_dir = Path(args.seed_dir)
    contexts = load_jsonl(seed_dir / "contexts.jsonl")
    injections = load_jsonl(seed_dir / "injections.jsonl")
    obfs = [o.strip() for o in args.obfuscations.split(",") if o.strip()]

    cases = build_cases(contexts, injections, obfs, seed=args.seed)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(
        f"{len(cases)}개 케이스 생성 -> {out}  "
        f"(문서 {len(contexts)} x 인젝션 {len(injections)} x 위치 {len(POSITIONS)} x 난독화 {len(obfs)})"
    )


if __name__ == "__main__":
    main()

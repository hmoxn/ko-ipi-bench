"""결과 파일들을 모아 공격 성공률(ASR, Attack Success Rate)을 축별로 집계합니다.

사용법:
  python -m kipi.report results/*.jsonl --by obfuscation
  python -m kipi.report results/*.jsonl --by model,defense --csv results/summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+")
    p.add_argument("--by", default="model,defense", help="집계 기준 축 (쉼표 구분)")
    p.add_argument("--csv", default="")
    args = p.parse_args()

    keys = [k.strip() for k in args.by.split(",") if k.strip()]
    groups: dict[tuple, list[bool]] = defaultdict(list)
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    groups[tuple(r[k] for k in keys)].append(bool(r["success"]))

    rows = [
        (*g, len(v), sum(v), 100.0 * sum(v) / len(v))
        for g, v in sorted(groups.items())
    ]

    header = [*keys, "n", "success", "ASR(%)"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for r in rows:
        print("| " + " | ".join([*map(str, r[:-1]), f"{r[-1]:.1f}"]) + " |")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        print(f"\nCSV 저장 -> {args.csv}")


if __name__ == "__main__":
    main()

"""테스트 케이스를 모델에 보내고 응답과 공격 성공 여부를 저장합니다.

백엔드:
  openai      : OpenAI 호환 /v1/chat/completions API (Ollama, vLLM, LM Studio 등 로컬 서버 포함)
  dummy-safe  : 항상 정상 요약만 하는 가짜 모델 (파이프라인 점검용)
  dummy-vuln  : 인젝션을 그대로 따르는 가짜 모델 (채점 로직 점검용)

예시 (Ollama 로컬 서버):
  python -m kipi.run_eval --backend openai --base-url http://localhost:11434/v1 \\
      --model qwen2.5:7b --defense none --out results/qwen2.5-7b_none.jsonl

외부 라이브러리 없이 파이썬 표준 라이브러리만 사용합니다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path

from .defenses import DEFENSES
from .judge import judge, normalize


# --- 백엔드 ------------------------------------------------------------------

def call_openai(messages, model, base_url, api_key, temperature=0.0, max_tokens=512, retries=3):
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"] or ""
        except Exception as e:  # 네트워크 오류 등은 잠깐 쉬었다 재시도
            if attempt == retries - 1:
                raise
            print(f"  재시도 {attempt + 1}/{retries}: {e}")
            time.sleep(2 ** attempt)
    return ""


def call_dummy_safe(messages, **_):
    return "요청하신 문서의 핵심 내용을 요약했습니다."


_CANARY_RE = re.compile(r"KIPI.{0,12}?([0-9A-F]{6})")


def call_dummy_vuln(messages, **_):
    text = normalize(messages[-1]["content"])
    if "영어" in text:
        return "Sure. Here is the answer in English only."
    m = _CANARY_RE.search(text)
    return f"요약입니다. KIPI{m.group(1)}" if m else "요약입니다."


BACKENDS = {"openai": call_openai, "dummy-safe": call_dummy_safe, "dummy-vuln": call_dummy_vuln}


# --- 메인 루프 ---------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cases", default="data/build/cases.jsonl")
    p.add_argument("--backend", choices=BACKENDS, default="dummy-safe")
    p.add_argument("--model", default="dummy")
    p.add_argument("--base-url", default="http://localhost:11434/v1")
    p.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    p.add_argument("--defense", choices=DEFENSES, default="none")
    p.add_argument("--limit", type=int, default=0, help="앞에서부터 N개만 실행 (0=전부)")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    with open(args.cases, encoding="utf-8") as f:
        cases = [json.loads(l) for l in f if l.strip()]
    if args.limit:
        cases = cases[: args.limit]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # 이어서 실행(resume): 이미 끝난 케이스는 건너뜀
    done = set()
    if out.exists():
        with out.open(encoding="utf-8") as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}

    call = BACKENDS[args.backend]
    build_messages = DEFENSES[args.defense]
    n_success = 0
    todo = [c for c in cases if c["id"] not in done]
    print(f"총 {len(cases)}개 중 {len(todo)}개 실행 (backend={args.backend}, model={args.model}, defense={args.defense})")

    with out.open("a", encoding="utf-8") as f:
        for i, case in enumerate(todo, 1):
            messages = build_messages(case)
            output = call(messages, model=args.model, base_url=args.base_url, api_key=args.api_key)
            success = judge(case, output)
            n_success += success
            record = {
                "id": case["id"],
                "model": args.model,
                "defense": args.defense,
                "goal": case["goal"],
                "register": case["register"],
                "position": case["position"],
                "obfuscation": case["obfuscation"],
                "context_type": case["context_type"],
                "success": success,
                "output": output,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            if i % 20 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}  현재까지 공격 성공 {n_success}")


if __name__ == "__main__":
    main()

"""한국어 특화 난독화(obfuscation) 변환 함수 모음.

모든 함수는 (text, rng) -> str 형태이며, 시드가 고정된 random.Random 을 받아
같은 입력이면 항상 같은 결과를 내도록 만들었습니다 (실험 재현성).
"""

from __future__ import annotations

import random
import re
from typing import Callable, Dict

# --- 한글 유니코드 상수 -------------------------------------------------------
# 완성형 한글 음절: U+AC00(가) ~ U+D7A3(힣)
# 음절 = 0xAC00 + (초성 * 21 + 중성) * 28 + 종성
SYLLABLE_BASE = 0xAC00
SYLLABLE_LAST = 0xD7A3

CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"  # 19개
JUNGSEONG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"  # 21개
JONGSEONG = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
    "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]  # 28개 (0번은 받침 없음)

ZERO_WIDTH_SPACE = "​"


def is_hangul_syllable(ch: str) -> bool:
    return SYLLABLE_BASE <= ord(ch) <= SYLLABLE_LAST


def decompose(ch: str) -> str:
    """완성형 음절 한 글자를 자모 문자열로 분해합니다. 예: '한' -> 'ㅎㅏㄴ'"""
    if not is_hangul_syllable(ch):
        return ch
    idx = ord(ch) - SYLLABLE_BASE
    cho, rest = divmod(idx, 21 * 28)
    jung, jong = divmod(rest, 28)
    return CHOSEONG[cho] + JUNGSEONG[jung] + JONGSEONG[jong]


# --- 난독화 변환 ---------------------------------------------------------------

def none(text: str, rng: random.Random) -> str:
    """변환 없음 (기준선)."""
    return text


def jamo_split(text: str, rng: random.Random, ratio: float = 0.5) -> str:
    """한글 음절의 일부(ratio)를 자모로 풀어 씁니다. 예: '무시해' -> 'ㅁㅜ시ㅎㅐ'"""
    return "".join(
        decompose(ch) if is_hangul_syllable(ch) and rng.random() < ratio else ch
        for ch in text
    )


def zero_width(text: str, rng: random.Random, ratio: float = 0.5) -> str:
    """글자 사이에 눈에 보이지 않는 zero-width space 를 끼워 넣습니다."""
    out = []
    for ch in text:
        out.append(ch)
        if not ch.isspace() and rng.random() < ratio:
            out.append(ZERO_WIDTH_SPACE)
    return "".join(out)


def syllable_spacing(text: str, rng: random.Random) -> str:
    """한글 음절 사이마다 공백을 넣습니다. 예: '무시하고' -> '무 시 하 고'"""
    out = []
    for i, ch in enumerate(text):
        out.append(ch)
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if is_hangul_syllable(ch) and nxt and is_hangul_syllable(nxt):
            out.append(" ")
    return "".join(out)


OBFUSCATIONS: Dict[str, Callable[[str, random.Random], str]] = {
    "none": none,
    "jamo_split": jamo_split,
    "zero_width": zero_width,
    "syllable_spacing": syllable_spacing,
}


def apply(name: str, text: str, rng: random.Random, protect: tuple = ()) -> str:
    """난독화를 적용합니다.

    protect 로 지정한 문자열들(예: 카나리 조각)은 변형되지 않도록 그대로 보존합니다.
    그래야 채점할 때 모델 출력에서 정확한 문자열을 찾을 수 있습니다.
    """
    fn = OBFUSCATIONS[name]
    protect = tuple(p for p in protect if p)
    if not protect:
        return fn(text, rng)
    pattern = "(" + "|".join(re.escape(p) for p in protect) + ")"
    pieces = re.split(pattern, text)
    return "".join(p if p in protect else fn(p, rng) for p in pieces)

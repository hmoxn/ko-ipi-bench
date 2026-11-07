# 처음 쓰는 사람을 위한 Git & GitHub 가이드

이 프로젝트를 올리면서 필요한 것만 순서대로 정리했습니다.

## 1. 준비

1. [github.com](https://github.com) 가입. 아이디는 이력서에 들어가니 실명이나 깔끔한 닉네임 추천
2. Git 설치: [git-scm.com](https://git-scm.com) (macOS는 터미널에서 `git --version` 입력 시 설치 안내가 나옴)
3. 내 정보 등록 (처음 한 번만)

```bash
git config --global user.name "홍길동"
git config --global user.email "GitHub에-가입한-이메일"
```

4. 인증: 요즘은 비밀번호 대신 **GitHub CLI** 로 로그인하는 게 가장 쉽습니다.

```bash
# https://cli.github.com 에서 gh 설치 후
gh auth login
```

## 2. 프로필 꾸미기 (10분)

- 프로필 사진, 소개 한 줄 ("AI Security에 관심 있는 컴퓨터공학 학부생")
- 내 아이디와 **같은 이름의 레포**를 만들면 그 README가 프로필 첫 화면에 표시됩니다. 관심 분야, 진행 중인 프로젝트, 연락처 정도면 충분해요.

## 3. 이 프로젝트를 첫 커밋으로 올리기

```bash
cd ko-ipi-bench
git init
git add .
git commit -m "Initial commit: KIPI-Bench 초기 구조"

# GitHub에 레포를 만들고 바로 연결 & 업로드
gh repo create ko-ipi-bench --public --source=. --push
```

웹에서 하고 싶다면: GitHub에서 New repository → 이름 입력 → **README 추가하지 말고** 생성 → 화면에 나오는 `git remote add origin ...`, `git push -u origin main` 두 줄 실행.

## 4. 매일 쓰는 명령어 4개

```bash
git status                 # 무엇이 바뀌었는지 확인
git add <파일>             # 커밋할 파일 선택 (전부: git add .)
git commit -m "메시지"     # 변경 내용을 기록
git push                   # GitHub에 업로드
```

**커밋 메시지 습관** (작은 단위로 자주!)

```
feat: 학과 공지 문서 5개 추가
fix: zero_width 난독화가 카나리를 깨뜨리는 문제 수정
docs: 관련 연구 정리 추가
exp: qwen2.5-7b 방어 기법 비교 결과
```

> 💡 GitHub 프로필의 잔디(contribution graph)는 꾸준함을 보여 줍니다. 몰아서 한 번에 올리기보다 작업한 날마다 커밋하세요.

## 5. 한 단계 더: 브랜치와 Pull Request

오픈소스 기여를 하려면 꼭 필요한 흐름이라, 내 레포에서 먼저 연습해 두면 좋아요.

```bash
git switch -c add-obfuscation-choseong   # 새 브랜치 만들고 이동
# ... 코드 수정 ...
git add . && git commit -m "feat: 초성 난독화 추가"
git push -u origin add-obfuscation-choseong
gh pr create --fill                      # Pull Request 생성
```

GitHub에서 PR을 열어 변경 내용을 확인한 뒤 **Merge** 하면 됩니다.

## 6. Issue로 할 일 관리하기

- 해야 할 일, 궁금한 점, 버그를 Issue로 등록 → 커밋 메시지에 `#3` 처럼 번호를 적으면 자동으로 연결
- `docs/ROADMAP.md`의 체크리스트를 Issue로 옮겨 두면 진행 상황이 레포에 그대로 남아 포트폴리오가 됩니다

## 7. 올리면 안 되는 것

- API 키, 비밀번호, `.env` 파일 → 실수로 올렸다면 **키를 즉시 폐기**하고 새로 발급 (커밋을 지워도 기록이 남을 수 있음)
- 대용량 모델 파일, 개인정보가 담긴 데이터
- `.gitignore`에 이미 기본 항목이 들어 있습니다

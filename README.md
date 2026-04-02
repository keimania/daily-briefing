# Daily Briefing - KRX Exchange & AI News

매일 아침 글로벌 거래소/금융 뉴스 및 AI 소식을 자동 수집하여 Obsidian 호환 마크다운으로 생성하는 시스템.

## Architecture

```
GitHub Actions (cron: 07:00 KST daily)
  -> Python RSS Collector (feedparser)
  -> Gemini API (summarize + translate EN/KR)
  -> Obsidian-compatible .md file
  -> Git commit & push
  -> Obsidian Git Sync -> Mobile
```

## Setup Guide / 설정 가이드

### 1. GitHub Repository 생성

```bash
# 로컬에서 Git 초기화
cd /path/to/daily
git init
git add .
git commit -m "Initial commit: daily briefing system"

# GitHub에서 새 private repo 생성 후
git remote add origin https://github.com/YOUR_USERNAME/daily-briefing.git
git branch -M main
git push -u origin main
```

### 2. GitHub Secrets 설정

GitHub repo -> Settings -> Secrets and variables -> Actions -> New repository secret:

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급한 Gemini API 키 |

### 3. Gemini API 키 발급

1. https://aistudio.google.com/apikey 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 키를 GitHub Secrets에 `GEMINI_API_KEY`로 등록

> Gemini 2.0 Flash 무료 티어: 분당 15회, 일 1,500회 요청 가능.
> 일 1회 브리핑 생성에는 충분합니다. **완전 무료.**

### 4. Obsidian 연동 (모바일 확인)

**방법 A: Obsidian Git 플러그인 (추천)**

1. Obsidian에서 Community Plugins -> "Obsidian Git" 설치
2. 이 GitHub 리포를 Obsidian vault로 설정
3. 자동 pull 간격 설정 (예: 30분)
4. 모바일 Obsidian에서도 동일하게 설정

**방법 B: GitHub Mobile 앱**

1. GitHub Mobile 앱 설치
2. 해당 리포의 `briefings/` 폴더에서 직접 md 파일 열람

### 5. 수동 실행 (테스트)

```bash
# 로컬 테스트
export GEMINI_API_KEY="your-key-here"
cd scripts
pip install -r ../requirements.txt
python main.py
```

GitHub Actions에서 수동 실행:
- repo -> Actions -> "Daily Briefing Generator" -> Run workflow

### 6. RSS 소스 커스터마이징

`scripts/rss_sources.py` 파일에서 RSS 피드를 추가/수정할 수 있습니다.

## File Structure

```
daily/
├── .github/workflows/
│   └── daily-briefing.yml    # GitHub Actions 워크플로우
├── briefings/
│   ├── latest.md             # 최신 브리핑 링크
│   └── 2026/
│       └── 03/
│           └── 2026-03-30-daily-briefing.md
├── scripts/
│   ├── main.py               # 메인 실행 스크립트
│   ├── rss_sources.py        # RSS 피드 소스 목록
│   ├── collect_news.py       # RSS 수집 모듈
│   └── summarizer.py         # Gemini API 요약/번역 모듈
├── templates/
│   └── daily-briefing-template.md
├── requirements.txt
└── README.md
```

## Cost Estimate / 비용 추정

| 항목 | 비용 |
|------|------|
| GitHub Actions | 무료 (월 2,000분, 일 ~2분 사용) |
| Gemini API (3 Flash) | **무료** (일 1,500회 제한, 1회만 사용) |
| Obsidian | 무료 (Sync 미사용 시) |
| **총 월 비용** | **$0 (완전 무료)** |

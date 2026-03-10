# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Kids learning quiz hub — no build step, no dependencies, no package manager. Every quiz is a single self-contained `index.html`.

**Live URL:** `https://vishalsingla2004.github.io/kids/`
**Repo:** `https://github.com/vishalsingla2004/kids.git` (GitHub Pages auto-deploys from `main`)

## Folder Structure

```
index.html              ← hub landing page (links to all quizzes)
report.html             ← parent progress report (shows mastery + points + $ value)
gen_dump.py             ← dumps all questions to questions_dump.txt

games/
  princess/             ← Princess Counting (ages 3-6, no points)
  soccer/               ← Soccer Quiz (ages 10+, no points)

5th-grade/
  math/                 ← SBA Math (509 q)
    area-2d/            ← Mastery: Area of 2D Shapes (150 q)
    circles/            ← Mastery: Circles — circumference & area (160 q)
    volume-3d/          ← Mastery: Volume of 3D Shapes (156 q)
  ela/                  ← SBA English (500 q)
  science/              ← SBA Science (501 q)

6th-grade/
  chemistry/            ← Chemistry (501 q)
  physics/              ← Physics (500 q)
  maths/                ← Maths (501 q)
  environmental/        ← Environmental Science (500 q)
  biology/              ← Biology (501 q)
  nsc/                  ← NSC Science Bowl (499 q)
```

## Deployment

```bash
git add -p
git commit -m "your message"
git push
```

## Quiz Architecture

Each quiz file is fully self-contained (CSS + HTML + JS in one file). Key patterns:

### Data
```js
const ALL_QUESTIONS = [
  { level:1|2|3, visual:'emoji', question:'...', options:['A','B','C'], answer:'A', fact:'...' }
];
const QUIZ_KEY = 'kids_q_<name>';  // localStorage key for mastery tracking
```
- 500+ questions for SBA/6th-grade quizzes; 150–160 for mastery sub-topics
- 3 levels: L1=easy, L2=medium, L3=hard (~equal split)
- `options` always has exactly 3 choices; `answer` must exactly match one option

### Session flow
```
init() → pickSession() → buildDots() → showQuestion() → handleAnswer()
       → showFeedback() → [dismissFeedback()] → advanceQuestion()
       → showLevelUp() (after Q5 and Q10) → showEndScreen()
```

- **`pickSession()`** — picks 5 questions per level (15 total), prioritizing unseen (unmastered) first
- **`buildDots()`** — MUST iterate `sessionQ` not `ALL_QUESTIONS` (critical: iterating ALL_QUESTIONS breaks layout by rendering 500+ dots)
- **`showFeedback(isCorrect, fact, chosen, correct)`** — correct: auto-dismiss timer ring; wrong: stays until tap. Wrong overlay shows: question text, chosen answer (red), correct answer (green)
- **`showEndScreen()`** — awards tiered points, shows rank

### Points system (all quizzes except soccer & princess)
Shared `localStorage` key: `kids_points`

```js
const POINTS_KEY = 'kids_points';
function getPoints() { return parseInt(localStorage.getItem(POINTS_KEY)||'0'); }
function addPoints(n) { localStorage.setItem(POINTS_KEY, getPoints()+n); }
function updatePtsDisplay() { const el=document.getElementById('ptsDisplay'); if(el) el.textContent='⭐ '+getPoints(); }
```

Points awarded in `showEndScreen()`:
- All 5 easy correct (`e===5`) → +1 pt
- All 5 medium correct (`m===5`) → +3 pts
- All 5 hard correct (`h===5`) → +6 pts
- Max per session: 10 pts. Points accumulate across all quiz sections.

Header shows live `⭐ N` pill (`id="ptsDisplay"`, class `pts-pill`). Call `updatePtsDisplay()` at end of `init()`.

### Wrong-answer detail overlay
Inside `#feedbackBox`, after `#tapHint`:
```html
<div class="wrong-detail" id="wrongDetail" style="display:none">
  <div class="wd-question" id="wdQuestion"></div>
  <div class="wd-row"><span class="wd-label">You chose:</span> <span class="wd-you" id="wdChosen"></span></div>
  <div class="wd-row"><span class="wd-label">Correct answer:</span> <span class="wd-correct" id="wdCorrect"></span></div>
</div>
```
Populated in `showFeedback()` wrong branch; hidden in correct branch.

### Back-button depth
- Depth-2 quizzes (`5th-grade/math/`, `6th-grade/chemistry/` etc.): `href="../../"`
- Depth-3 mastery quizzes (`5th-grade/math/area-2d/` etc.): `href="../../../"`

### Mastery tracking
```js
function getMastered(){try{return new Set(JSON.parse(localStorage.getItem(QUIZ_KEY)||'[]'));}catch{return new Set();}}
function markMastered(idx){try{const m=JSON.parse(localStorage.getItem(QUIZ_KEY)||'[]');if(!m.includes(idx)){m.push(idx);localStorage.setItem(QUIZ_KEY,JSON.stringify(m));}}catch{}}
```
`idx` is the index into `ALL_QUESTIONS`. Mastered questions are shown last in `pickSession()`.

### CSS theme variables
Each quiz sets `--c1` (dark bg), `--c2` (mid bg), `--acc` (accent color):
- SBA Math / mastery topics: `#0a1628 / #1a3a6b / #60a5fa` (blue)
- SBA ELA: `#1a0a2e / #4a1a6b / #c084fc` (purple)
- SBA Science: `#0d2818 / #1a4a2e / #4ade80` (green)
- Chemistry: `#1a003d / #4a0080 / #c471ed` (purple-violet)
- Physics: `#001a33 / #003580 / #4facfe` (blue)
- Maths (6th): `#2d1000 / #7a3200 / #f39c12` (orange)
- Environmental: `#001426 / #00354f / #26c6da` (teal)
- Biology: `#001a0d / #004d28 / #4caf50` (green)
- NSC: `#060d1f / #0d2560 / #38bdf8` (sky blue)

## Hub & Report

**`index.html`** — links to all quizzes; shows live `⭐ N points` from `kids_points` via inline `<script>` in header. Sections: 🎮 Games, 🔬 6th Grade Science, 🏆 Competition Prep, 📝 5th Grade SBA Practice, 📐 Math Mastery Topics.

The hub script uses `applyHubState()` called on both initial load and `pageshow` (handles browser back-forward cache):
```js
function applyHubState() {
  // update points display
  document.querySelectorAll('[data-tile]').forEach(c => c.style.display = '');  // reset all first
  const hidden = JSON.parse(localStorage.getItem('kids_hidden_tiles') || '[]');
  hidden.forEach(id => { const c = document.querySelector('[data-tile="'+id+'"]'); if(c) c.style.display='none'; });
}
applyHubState();
window.addEventListener('pageshow', applyHubState);  // fires on bfcache restore too
```
Every card `<a>` has a `data-tile="<id>"` attribute. IDs: `princess`, `soccer`, `sba-math`, `sba-ela`, `sba-science`, `area-2d`, `circles`, `volume-3d`, `chemistry`, `physics`, `maths`, `environmental`, `biology`, `nsc`.

**`report.html`** — parent-only view. Contains:
- Mastery stats per subject (`SUBJECTS` array drives cards)
- Points box: total `⭐` + dollar value (10 pts = $1.00) — dollar amount shown here only, never in kid UI
- **Manage Tiles** panel: toggle switches to hide/show each hub card. State stored in `kids_hidden_tiles` (JSON array of hidden tile IDs). `initToggles()` reads current state on load.

## gen_dump.py

Dumps all quiz questions to `questions_dump.txt` for review. Run with:
```bash
python gen_dump.py
```
Add new quiz files to the `files` list inside the script when adding a new quiz.

## Adding a New Quiz

1. Create `<grade>/<subject>/index.html` — copy nearest existing quiz, change `QUIZ_KEY`, title, theme colors, `ALL_QUESTIONS`, and back-button depth.
2. Add a card in `index.html` hub with `data-tile="<new-id>"` attribute and correct `href`.
3. Add `<new-id>` to the `ALL_TILES` array in `report.html` and add a `.tile-row` toggle in the Manage Tiles HTML.
4. Add entry to `SUBJECTS` array in `report.html` with correct `total`, `easyN`, `medN`, `hardN`, `group`.
5. Add entry to `files` list in `gen_dump.py`.
6. Verify `buildDots()` uses `sessionQ` not `ALL_QUESTIONS`.

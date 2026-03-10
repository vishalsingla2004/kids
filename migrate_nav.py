#!/usr/bin/env python3
"""
migrate_nav.py — Adds back/forward question review navigation to all quiz files.

Changes applied to each file:
  1. CSS: .nav-arrow and .review-banner styles
  2. JS state: sessionAnswers, sessionShuffled, viewingIdx variables
  3. New functions: updateNavArrows, navBack, navForward, showPastQuestion
  4. init(): reset new state, add nav buttons + review banner to HTML template
  5. showQuestion(): save shuffled order, reset viewingIdx, hide banner, call updateNavArrows
  6. handleAnswer(): record chosen answer

Run: python migrate_nav.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

QUIZ_FILES = [
    '5th-grade/math/index.html',
    '5th-grade/math/area-2d/index.html',
    '5th-grade/math/circles/index.html',
    '5th-grade/math/volume-3d/index.html',
    '5th-grade/ela/index.html',
    '5th-grade/science/index.html',
    '6th-grade/chemistry/index.html',
    '6th-grade/physics/index.html',
    '6th-grade/maths/index.html',
    '6th-grade/environmental/index.html',
    '6th-grade/biology/index.html',
    '6th-grade/nsc/index.html',
]

NAV_CSS = """\
  .nav-arrow{position:fixed;top:50%;transform:translateY(-50%);width:44px;height:88px;background:rgba(255,255,255,0.08);border:1.5px solid rgba(255,255,255,0.18);border-radius:12px;color:rgba(255,255,255,0.7);font-size:2.4rem;cursor:pointer;display:none;align-items:center;justify-content:center;z-index:20;-webkit-tap-highlight-color:transparent;touch-action:manipulation;transition:background 0.15s;}
  .nav-arrow:active{background:rgba(255,255,255,0.18);}
  #navPrev{left:4px;}
  #navNext{right:4px;}
  .review-banner{font-size:0.85rem;color:rgba(255,255,255,0.75);text-align:center;padding:5px 12px;margin-bottom:6px;background:rgba(255,255,255,0.1);border-radius:10px;}"""

NAV_STATE = "let sessionAnswers=[],sessionShuffled=[],viewingIdx=null;"

NAV_FUNCTIONS = """\
function updateNavArrows(){const p=document.getElementById('navPrev'),n=document.getElementById('navNext');if(!p)return;const idx=viewingIdx!==null?viewingIdx:current;p.style.display=idx>0?'flex':'none';n.style.display=(viewingIdx!==null&&viewingIdx<current)?'flex':'none';}
function navBack(){const idx=viewingIdx!==null?viewingIdx:current;if(idx>0)showPastQuestion(idx-1);}
function navForward(){if(viewingIdx===null)return;if(viewingIdx<current-1)showPastQuestion(viewingIdx+1);else{viewingIdx=null;showQuestion();}}
function showPastQuestion(idx){viewingIdx=idx;const q=sessionQ[idx];const badge=document.getElementById('levelBadge');if(q.level===1){badge.className='level-badge easy';badge.textContent='\\u2b50 Easy';}if(q.level===2){badge.className='level-badge medium';badge.textContent='\\u2b50\\u2b50 Medium';}if(q.level===3){badge.className='level-badge hard';badge.textContent='\\u2b50\\u2b50\\u2b50 Hard';}document.getElementById('visualCard').innerHTML='<span class="visual-emoji">'+q.visual+'</span>';document.getElementById('questionText').textContent=q.question;const shuffled=sessionShuffled[idx]||[...q.options];const chosen=sessionAnswers[idx];const correct=q.answer;const choicesEl=document.getElementById('choices');choicesEl.innerHTML='';['A','B','C'].forEach((letter,i)=>{const opt=shuffled[i];const btn=document.createElement('button');btn.className='choice-btn';btn.disabled=true;btn.style.cursor='default';if(opt===correct)btn.classList.add('correct');if(opt===chosen&&opt!==correct)btn.classList.add('wrong');btn.innerHTML='<span class="choice-letter">'+letter+'</span>'+opt;choicesEl.appendChild(btn);});const rb=document.getElementById('reviewBanner');if(rb){rb.style.display='';rb.textContent=dotResults[idx]==='correct'?'\\u2705 Q'+(idx+1)+' \\u00b7 Correct':'\\u274c Q'+(idx+1)+' \\u00b7 Incorrect';}document.getElementById('gameScreen').classList.remove('shake');updateNavArrows();}"""


def apply(path_str):
    path = ROOT / path_str
    if not path.exists():
        print(f"  SKIP (not found): {path_str}")
        return False

    text = path.read_text(encoding='utf-8')
    original = text
    ok = True

    # ── 1. CSS ──────────────────────────────────────────────────────────────
    if '.nav-arrow' in text:
        print(f"  SKIP css (already applied): {path_str}")
    elif '</style>' in text:
        text = text.replace('</style>', NAV_CSS + '\n</style>', 1)
    else:
        print(f"  WARN: no </style> in {path_str}")
        ok = False

    # ── 2. State variables ──────────────────────────────────────────────────
    if 'sessionAnswers' not in text:
        # Match: let current = 0, score = 0, dotResults = [], sessionQ = [];
        # or minified: let current=0,score=0,dotResults=[],sessionQ=[];
        m = re.search(r'(let current\s*=\s*0.*?;)', text)
        if m:
            text = text[:m.end()] + '\n' + NAV_STATE + text[m.end():]
        else:
            print(f"  WARN: state var pattern not found in {path_str}")
            ok = False

    # ── 3. New functions (before function init) ─────────────────────────────
    if 'function updateNavArrows' not in text:
        m = re.search(r'\nfunction init\s*\(\s*\)', text)
        if m:
            insert_at = m.start()
            text = text[:insert_at] + '\n' + NAV_FUNCTIONS + text[insert_at:]
        else:
            print(f"  WARN: function init() not found in {path_str}")
            ok = False

    # ── 4a. init(): reset new state ─────────────────────────────────────────
    if 'sessionAnswers=Array(15)' not in text and 'sessionAnswers = Array(15)' not in text:
        # Find dotResults = Array(15).fill(null); in init body
        m = re.search(r'(dotResults\s*=\s*Array\s*\(15\)\s*\.fill\s*\(null\)\s*;)', text)
        if m:
            reset_addition = 'sessionAnswers=Array(15).fill(null);sessionShuffled=Array(15).fill(null);viewingIdx=null;'
            text = text[:m.end()] + reset_addition + text[m.end():]
        else:
            print(f"  WARN: dotResults init pattern not found in {path_str}")
            ok = False

    # ── 4b. init(): add HTML nav buttons after back-btn ─────────────────────
    NAV_BUTTONS = '<button class="nav-arrow" id="navPrev" onclick="navBack()">\\u2039</button><button class="nav-arrow" id="navNext" onclick="navForward()">\\u203a</button>'
    if 'id="navPrev"' not in text:
        # In the template literal, find: >← Home</a>
        # and insert nav buttons right after
        m = re.search(r'(>← Home</a>)', text)
        if m:
            text = text[:m.end()] + NAV_BUTTONS + text[m.end():]
        else:
            # Try alternate: >← Back</a>
            m = re.search(r'(>← Back</a>)', text)
            if m:
                text = text[:m.end()] + NAV_BUTTONS + text[m.end():]
            else:
                print(f"  WARN: back-btn anchor not found in {path_str}")
                ok = False

    # ── 4c. init(): add review banner before choices div ────────────────────
    REVIEW_BANNER = '<div class="review-banner" id="reviewBanner" style="display:none"></div>'
    if 'id="reviewBanner"' not in text:
        m = re.search(r'(<div class="choices" id="choices"></div>)', text)
        if m:
            text = text[:m.start()] + REVIEW_BANNER + text[m.start():]
        else:
            print(f"  WARN: choices div not found in {path_str}")
            ok = False

    # ── 5a. showQuestion(): reset viewingIdx + hide banner at function start ─
    sq_check = text.split('function showQuestion')[1] if 'function showQuestion' in text else ''
    if 'viewingIdx=null' not in sq_check.split('\nfunction ')[0]:
        # Find: function showQuestion() { OR function showQuestion(){
        m = re.search(r'(function showQuestion\s*\(\s*\)\s*\{)', text)
        if m:
            insert = 'viewingIdx=null;const rb=document.getElementById(\'reviewBanner\');if(rb)rb.style.display=\'none\';'
            text = text[:m.end()] + insert + text[m.end():]
        else:
            print(f"  WARN: showQuestion not found in {path_str}")
            ok = False

    # ── 5b. showQuestion(): save shuffled order ─────────────────────────────
    if 'sessionShuffled[current]=shuffled' not in text:
        # Find: const shuffled=shuffle([...q.options]);
        m = re.search(r'(const shuffled\s*=\s*shuffle\s*\(\s*\[\s*\.\.\.q\.options\s*\]\s*\)\s*;)', text)
        if m:
            text = text[:m.end()] + 'sessionShuffled[current]=shuffled;' + text[m.end():]
        else:
            print(f"  WARN: shuffled pattern not found in {path_str}")
            ok = False

    # ── 5c. showQuestion(): call updateNavArrows at end ─────────────────────
    if 'updateNavArrows' not in text.split('function showQuestion')[1].split('function ')[0] if 'function showQuestion' in text else True:
        # Find: classList.remove('shake'); at end of showQuestion
        # Add updateNavArrows() after it — only the first occurrence after showQuestion
        sq_start = text.find('function showQuestion')
        if sq_start != -1:
            # Find next function definition after showQuestion
            next_fn = re.search(r'\nfunction ', text[sq_start+20:])
            sq_end = sq_start + 20 + (next_fn.start() if next_fn else len(text))
            sq_body = text[sq_start:sq_end]
            # Find the classList.remove('shake') in showQuestion body
            m = re.search(r"(document\.getElementById\('gameScreen'\)\.classList\.remove\('shake'\);)", sq_body)
            if m:
                insert_pos = sq_start + m.end()
                if 'updateNavArrows()' not in text[insert_pos:insert_pos+50]:
                    text = text[:insert_pos] + 'updateNavArrows();' + text[insert_pos:]
            else:
                print(f"  WARN: shake removal not found in showQuestion of {path_str}")

    # ── 6. handleAnswer(): save chosen answer ───────────────────────────────
    if 'sessionAnswers[current]=chosen' not in text:
        # Find: const isCorrect = chosen===correct; or const isCorrect=chosen===correct;
        m = re.search(r'(const isCorrect\s*=\s*chosen===correct\s*;)', text)
        if m:
            text = text[:m.end()] + 'sessionAnswers[current]=chosen;' + text[m.end():]
        else:
            print(f"  WARN: isCorrect pattern not found in {path_str}")
            ok = False

    if text == original:
        print(f"  NO CHANGE: {path_str}")
        return True

    path.write_text(text, encoding='utf-8')
    status = "OK" if ok else "PARTIAL"
    print(f"  [{status}] {path_str}")
    return ok


def main():
    print("Applying navigation changes to quiz files...\n")
    results = []
    for f in QUIZ_FILES:
        results.append(apply(f))
    print(f"\nDone. {sum(results)}/{len(results)} files updated successfully.")


if __name__ == '__main__':
    main()

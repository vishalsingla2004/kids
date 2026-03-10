#!/usr/bin/env python3
"""
validate.py — Structural validation for all quiz questions.

Checks every question for:
  - answer exactly matches one of the 3 options
  - exactly 3 options
  - level is 1, 2, or 3
  - required fields present (level, question, options, answer, fact, visual)
  - no duplicate question text within a file

Requires Node.js to parse the JS question arrays.

Usage:
  python validate.py                    # check all files
  python validate.py chemistry          # check files matching 'chemistry'
"""

import subprocess, json, sys, io
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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

# Node.js script: extracts ALL_QUESTIONS as JSON by bracket-counting
_EXTRACT_JS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const marker = 'const ALL_QUESTIONS = ';
const start = html.indexOf(marker);
if (start === -1) { console.log('[]'); process.exit(0); }
let depth = 0; let i = start + marker.length;
let inStr = false, strChar = null, escape = false;
for (; i < html.length; i++) {
  const c = html[i];
  if (escape) { escape = false; continue; }
  if (c === '\\') { escape = true; continue; }
  if (inStr) { if (c === strChar) inStr = false; continue; }
  if (c === '"' || c === "'") { inStr = true; strChar = c; continue; }
  if (c === '[') depth++;
  if (c === ']') { depth--; if (depth === 0) { i++; break; } }
}
const arrText = html.slice(start + marker.length, i);
try {
  const ALL_QUESTIONS = eval(arrText);
  console.log(JSON.stringify(ALL_QUESTIONS));
} catch(e) {
  process.stderr.write('Parse error: ' + e.message + '\n');
  console.log('[]');
}
"""


def check_node():
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: Node.js not found. Install Node.js to run this validator.")
        sys.exit(1)


def extract_questions(path):
    r = subprocess.run(
        ['node', '-e', _EXTRACT_JS, str(path)],
        capture_output=True, text=True, encoding='utf-8'
    )
    if r.stderr:
        print(f"  Node error: {r.stderr.strip()}")
    try:
        return json.loads(r.stdout or '[]')
    except json.JSONDecodeError:
        return []


def check_file(rel_path):
    path = ROOT / rel_path
    if not path.exists():
        print(f"\n[SKIP] {rel_path} — file not found")
        return 0

    questions = extract_questions(path)
    if not questions:
        print(f"\n[WARN] {rel_path} — no questions extracted")
        return 0

    errors = []
    seen = {}
    level_counts = {1: 0, 2: 0, 3: 0}

    for i, q in enumerate(questions):
        num = i + 1

        # Required fields
        for field in ('level', 'question', 'options', 'answer', 'fact', 'visual'):
            if field not in q:
                errors.append(f"Q{num}: missing field '{field}'")

        # Valid level
        lvl = q.get('level')
        if lvl not in (1, 2, 3):
            errors.append(f"Q{num}: invalid level {lvl!r} (must be 1, 2, or 3)")
        else:
            level_counts[lvl] += 1

        # Exactly 3 options
        opts = q.get('options', [])
        if not isinstance(opts, list) or len(opts) != 3:
            errors.append(f"Q{num}: options must be a list of 3, got {len(opts) if isinstance(opts, list) else type(opts).__name__}")
        elif 'answer' in q and q['answer'] not in opts:
            errors.append(
                f"Q{num}: answer not in options\n"
                f"         answer:  {q['answer']!r}\n"
                f"         options: {opts}"
            )

        # Duplicate detection
        if 'question' in q:
            key = q['question'].strip().lower()
            if key in seen:
                errors.append(f"Q{num}: duplicate of Q{seen[key]+1}: {q['question'][:70]!r}")
            else:
                seen[key] = i

    l1, l2, l3 = level_counts[1], level_counts[2], level_counts[3]
    status = '✓' if not errors else '✗'
    print(f"\n{status} {rel_path}  ({len(questions)}q  L1={l1} L2={l2} L3={l3})")
    for e in errors:
        print(f"    ERROR: {e}")

    return len(errors)


def main():
    check_node()
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    files = [f for f in QUIZ_FILES if not filter_arg or filter_arg in f]

    if not files:
        print(f"No files matched '{filter_arg}'")
        sys.exit(1)

    total_errors = 0
    for f in files:
        total_errors += check_file(f)

    print(f"\n{'─' * 55}")
    if total_errors == 0:
        print(f"✓ All {len(files)} file(s) passed structural validation.")
    else:
        print(f"✗ {total_errors} error(s) found. Fix them before deploying.")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Book & Screenplay Color Converter
Reads any plain text book or movie script, finds the color words in each chapter,
and saves the color segments into gallery_previews.json for p5.js to draw.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# -----------------------------------------------------------------------------
# 1. Color Dictionary
# Maps everyday color words to their visual hex codes for the canvas.
# -----------------------------------------------------------------------------
COLOR_MAP = {
    'red': '#ef4444', 'crimson': '#dc2626', 'scarlet': '#f43f5e', 'maroon': '#7f1d1d',
    'ruby': '#e0115f', 'rose': '#ff007f', 'coral': '#fb7185', 'pink': '#f472b6',
    'magenta': '#ec4899', 'rust': '#b7410e', 'copper': '#b87333', 'bronze': '#cd7f32',
    'auburn': '#a52a2a', 'mahogany': '#c04000', 'chestnut': '#954535', 'orange': '#fb923c',
    'peach': '#fdba74', 'amber': '#f59e0b', 'gold': '#f59e0b', 'yellow': '#eab308',
    'mustard': '#ffdb58', 'ochre': '#cc7722', 'ocher': '#cc7722', 'green': '#22c55e',
    'lime': '#84cc16', 'olive': '#4d7c0f', 'emerald': '#50c878', 'teal': '#0d9488',
    'blue': '#3b82f6', 'navy': '#1e3a8a', 'azure': '#0ea5e9', 'cyan': '#06b6d4',
    'sapphire': '#0f52ba', 'turquoise': '#40e0d0', 'indigo': '#6366f1', 'purple': '#a855f7',
    'violet': '#8b5cf6', 'lavender': '#c4b5fd', 'plum': '#8e4585', 'lilac': '#c8a2c8',
    'brown': '#a16207', 'beige': '#f5f5dc', 'tan': '#d2b48c', 'khaki': '#c3b091',
    'sand': '#d4b886', 'dust': '#b0a48a', 'sepia': '#704214', 'chocolate': '#7b3f00',
    'hazel': '#8e7618', 'cream': '#fffdd0', 'black': '#111827', 'ebony': '#282828',
    'charcoal': '#36454f', 'white': '#e5e7eb', 'ivory': '#fffff0', 'snow': '#f8f9fa',
    'pearl': '#eaedec', 'gray': '#6b7280', 'grey': '#6b7280', 'silver': '#9ca3af',
    'ash': '#b2beb5', 'slate': '#708090', 'brass': '#b5a642'
}

CANON_KEYS = [k if k != 'grey' else 'gray' for k in COLOR_MAP.keys()]
TOKENS = sorted(list(set(CANON_KEYS)), key=lambda x: -len(x))
TOKEN_PAT = '|'.join([re.escape(k) for k in TOKENS])
SUFFIX_PAT = r'(?:-ish|ish|-ened|ened|-dened|dened|-ening|ening|-dening|dening|-ness|ness|-dness|dness|-ed|ed|-ded|ded|-ing|ing|-ding|ding|-en|en|-den|den|-y|y)?'

COLOR_REGEX = re.compile(
    rf'(?:^|[^A-Za-z])((?:{TOKEN_PAT}){SUFFIX_PAT})(?=[^A-Za-z]|$)(?:[\-/]((?:{TOKEN_PAT}){SUFFIX_PAT})(?=[^A-Za-z]|$))?',
    re.IGNORECASE
)

# -----------------------------------------------------------------------------
# 2. Smart Filter
# Checks surrounding words to ignore action words that look like colors
# (for example: ignores "the sun rose" or "dust the table").
# -----------------------------------------------------------------------------
ROSE_VERB_PREPS = r'^\s*(?:from|into|onto|upon|above|to|up|out|after|over|off|in|against|among|towards|toward|by|with|through)\b'
ROSE_VERB_ADVERBS = r'^\s*(?:at\s+once|slowly|quickly|swiftly|gradually|suddenly|again|steeply|higher|taller|high|early|late|majestic|straight|upwards|upward|visibly|steadily|sharply)\b'
DETERMINERS_PREP_PAT = r'\b(?:a|an|my|his|her|its|their|your|our|some|any|each|every|no|many|few|much|more|most|pale|deep|dark|light|bright|soft|vivid|rich|dull|warm|cool|pure|faint|heavy|fine|coarse|dry|wet|wild|sweet|red|blue|green|yellow|white|bed\s+of)\s*$'

def normalize_color_token(tok):
    if not tok:
        return None
    t = re.sub(r'[^a-z]', '', tok.lower())
    if t in CANON_KEYS:
        return 'gray' if t == 'grey' else t
    for suf in ['ening', 'ened', 'dening', 'dened', 'ness', 'dness', 'ish', 'ing', 'ding', 'ed', 'ded', 'en', 'den', 'y']:
        if t.endswith(suf):
            cand = t[:-len(suf)]
            cand = 'gray' if cand == 'grey' else cand
            if cand in CANON_KEYS:
                return cand
    return None

def is_verb_context(token, left_ctx, right_ctx):
    token_lower = token.lower()
    left_str = left_ctx.lower().strip()
    right_str = right_ctx.lower().strip()

    if token_lower == 'rose':
        if re.search(r'^(?:-colored|-coloured|-tinted|-pink|-red|-velvet|-silk|-satin|-hue|-shade|-brambles|-leaf|-leaves|-petals)\b', right_str):
            return False
        if re.search(ROSE_VERB_PREPS, right_str) or re.search(ROSE_VERB_ADVERBS, right_str) or re.search(r'^\s*and\b', right_str):
            return True
        if re.search(DETERMINERS_PREP_PAT, left_str):
            return False
        if re.search(r'\b(?:he|she|it|they|we|you|i|who|this|these|those|also|both|then|now)\s*(?:all)?\s*$', left_str):
            return True
        if re.search(r'\b[a-z]{3,}\s*$', left_str):
            last_word = left_str.split()[-1]
            if last_word not in ['red', 'white', 'yellow', 'pink', 'pale', 'dark', 'sweet', 'wild', 'fresh', 'of', 'in', 'with', 'like', 'as']:
                return True
        return False

    if token_lower in ['dust', 'rust']:
        if re.search(r'\b(?:to|will|would|can|could|did)\s*$', left_str):
            return True
    return False

# -----------------------------------------------------------------------------
# 3. Clean and Split Text
# Removes standard ebook header/footer notices and splits into chapters/scenes.
# -----------------------------------------------------------------------------
def clean_text(text):
    lines = text.splitlines()
    start_i = 0
    end_i = len(lines)
    for i, line in enumerate(lines):
        if '*** START OF THE PROJECT GUTENBERG' in line or '*** START OF THIS PROJECT GUTENBERG' in line:
            start_i = i + 1
        if '*** END OF THE PROJECT GUTENBERG' in line or '*** END OF THIS PROJECT GUTENBERG' in line:
            end_i = i
    return '\n'.join(lines[start_i:end_i]) + '\n'

def is_screenplay_format(text):
    # Checks if this file looks like a movie script (INT. / EXT. scene headers)
    scene_pattern = re.compile(r'^\s*(?:INT/EXT\.|EXT/INT\.|INT\.|EXT\.)(?:\s|$)', re.MULTILINE | re.IGNORECASE)
    return len(scene_pattern.findall(text)) >= 5

def detect_chapters(text):
    if is_screenplay_format(text):
        # Movie script: group scenes into story chapters
        pattern = re.compile(r'^\s*(?:INT/EXT\.|EXT/INT\.|INT\.|EXT\.)(?:\s|$).*$', re.MULTILINE | re.IGNORECASE)
        scenes = [m.start() for m in pattern.finditer(text)]
        if not scenes:
            return [(0, len(text), 0)]
        group_size = max(3, len(scenes) // 15)
        spans = []
        for i, s in enumerate(scenes):
            e = scenes[i + 1] if i + 1 < len(scenes) else len(text)
            ch_idx = i // group_size
            spans.append((s, e, ch_idx))
        return spans
    else:
        # Novel: look for chapter headings like CHAPTER 1, BOOK I, etc.
        pattern = re.compile(
            r'^\s*(_?\s*(?:BOOK|Book|CHAPTER|Chapter|ACT|Act)\b.*_?|^\s*=\s*=\s*=\s*=\s*=\s*=$)\s*$',
            re.MULTILINE
        )
        starts = [m.start() for m in pattern.finditer(text)]
        if not starts:
            return [(0, len(text), 0)]
        spans = []
        for i, s in enumerate(starts):
            e = starts[i + 1] if i + 1 < len(starts) else len(text)
            spans.append((s, e, i))
        return spans

def detect_paragraphs(text):
    # Splits the story into natural paragraphs or dialogue blocks
    para_split = re.compile(r'(?:\r?\n){2,}|(?:\r?\n)(?=\s{2,}\S)')
    spans = []
    last = 0
    for m in para_split.finditer(text):
        if text[last:m.start()].strip():
            spans.append((last, m.start()))
        last = m.end()
    if last < len(text) and text[last:].strip():
        spans.append((last, len(text)))
    return spans

# -----------------------------------------------------------------------------
# 4. Color Extraction
# Scans each paragraph for color words and measures the passage length.
# -----------------------------------------------------------------------------
def extract_book_segments(text):
    text = clean_text(text)
    chapter_spans = detect_chapters(text)
    para_spans = detect_paragraphs(text)

    def get_chapter(pos):
        for s, e, ci in chapter_spans:
            if s <= pos < e:
                return ci
        return chapter_spans[-1][2] if chapter_spans else 0

    paras_segments = []

    for ps, pe in para_spans:
        para_text = text[ps:pe]
        para_len = max(1, pe - ps)
        c_idx = get_chapter(ps)

        matches = []
        for m in COLOR_REGEX.finditer(para_text):
            for g_idx in (1, 2):
                tok = m.group(g_idx)
                norm = normalize_color_token(tok)
                if norm:
                    m_start = m.start(g_idx)
                    m_end = m.end(g_idx)
                    left_c = para_text[max(0, m_start-40):m_start]
                    right_c = para_text[m_end:min(len(para_text), m_end+40)]
                    if not is_verb_context(norm, left_c, right_c):
                        matches.append({'start': m_start, 'end': m_end, 'hex': COLOR_MAP[norm]})

        # If a paragraph has colors, measure each color's share of the passage
        N = len(matches)
        if N == 1:
            paras_segments.append({'chapter_idx': c_idx, 'len': para_len, 'hex': matches[0]['hex']})
        elif N > 1:
            for i, match in enumerate(matches):
                seg_start = 0 if i == 0 else (matches[i-1]['end'] + match['start']) // 2
                seg_end = para_len if i == N - 1 else (match['end'] + matches[i+1]['start']) // 2
                seg_len = max(1, seg_end - seg_start)
                paras_segments.append({'chapter_idx': c_idx, 'len': seg_len, 'hex': match['hex']})

    # Group by chapter and combine neighboring segments with the same color
    by_chapter = defaultdict(list)
    for seg in paras_segments:
        by_chapter[seg['chapter_idx']].append(seg)

    book_preview = []
    for ci in sorted(by_chapter.keys()):
        ch_merged = []
        for seg in by_chapter[ci]:
            if ch_merged and ch_merged[-1][1] == seg['hex']:
                ch_merged[-1][0] += seg['len']
            else:
                ch_merged.append([seg['len'], seg['hex']])
        book_preview.append(ch_merged)

    return book_preview

# -----------------------------------------------------------------------------
# 5. Save Results
# Adds the new book directly into gallery_previews.json for p5.js.
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Convert a book or screenplay into color segments.")
    parser.add_argument("source", help="Path to text file (e.g. hamlet.txt)")
    parser.add_argument("--name", help="Display name for the book (e.g. Hamlet)")
    args = parser.parse_args()

    src_path = Path(args.source)
    if src_path.is_dir():
        candidate = src_path / "book.txt"
        if not candidate.exists():
            print(f"Error: Could not find book.txt inside {src_path}")
            sys.exit(1)
        src_path = candidate

    if not src_path.exists():
        print(f"Error: File not found: {src_path}")
        sys.exit(1)

    book_name = args.name or src_path.stem

    print(f"Reading '{src_path.name}'...")
    text = src_path.read_text(encoding='utf-8', errors='ignore')
    
    print(f"Extracting color words for '{book_name}'...")
    chapters_data = extract_book_segments(text)

    if not chapters_data:
        print("Warning: No color words found in the text.")
        sys.exit(1)

    json_path = Path(__file__).parent / "gallery_previews.json"
    if json_path.exists():
        previews = json.loads(json_path.read_text(encoding='utf-8'))
    else:
        previews = {}

    previews[book_name] = chapters_data
    json_path.write_text(json.dumps(previews, ensure_ascii=False), encoding='utf-8')

    total_segments = sum(len(ch) for ch in chapters_data)
    print(f"\nSuccess! Added '{book_name}' with {len(chapters_data)} chapters and {total_segments} color moments.")
    print(f"Saved to: {json_path.name}")
    print(f"\nNext step: Open sketch.js and change:\n  const BOOK = '{book_name}';\n")

if __name__ == "__main__":
    main()

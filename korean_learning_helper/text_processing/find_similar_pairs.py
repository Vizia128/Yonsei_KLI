"""
find_similar_pairs.py

Finds all pairs of TOPIK words that are identical except that exactly ONE
syllable differs by exactly ONE jamo component (초성 / 중성 / 종성).

Examples
--------
  소년 / 소녀   — same 소, then 년 vs 녀 differ only in 종성 ㄴ
  자라다 / 바라다 — same 라다, first syllable 자 vs 바 differ only in 초성

A Korean syllable block in [U+AC00, U+D7A3] decomposes as:
  code  = ord(ch) - 0xAC00
  초성  = code // 588        (21 possible initials)
  중성  = (code % 588) // 28 (21 possible vowels)
  종성  = code % 28          (28 slots: 0 = no final)

Two words match  iff:
  • same number of characters
  • every character is a Hangul syllable block
  • exactly 1 position differs
  • at that position the jamo-distance == 1

Ranking uses  score = 1 / sum(1/index)  (lower = more common words first).
Two outputs are written to  topik/similar_pairs/:
  similar_pairs_all.csv       — all words from topik_words.csv
  similar_pairs_my_words.csv  — words present in my_topik_words_anki.csv
                                 (ranked by Anki position)
"""

import csv
import os
from itertools import combinations

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT_FILE = r'topik_words.csv'
ANKI_FILE  = r'my_topik_words_anki.csv'
OUTPUT_DIR = r'similar_pairs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Hangul jamo decomposition
# ---------------------------------------------------------------------------
HANGUL_BASE = 0xAC00
CHOSUNG_MULTIPLIER = 588
JUNGSEONG_MULTIPLIER = 28

def is_syllable(ch: str) -> bool:
    """Checks if a character is a valid Hangul syllable block."""
    return 0xAC00 <= ord(ch) <= 0xD7A3

def decompose(ch: str) -> tuple[int, int, int]:
    """Return (초성, 중성, 종성) indices for a Hangul syllable block."""
    code = ord(ch) - HANGUL_BASE
    cho = code // CHOSUNG_MULTIPLIER
    jung = (code % CHOSUNG_MULTIPLIER) // JUNGSEONG_MULTIPLIER
    jong = code % JUNGSEONG_MULTIPLIER
    return cho, jung, jong

def jamo_distance(char_a: str, char_b: str) -> int:
    """Number of jamo components that differ between two syllables."""
    decomp_a, decomp_b = decompose(char_a), decompose(char_b)
    return sum(x != y for x, y in zip(decomp_a, decomp_b))

def single_jamo_apart(word_1: str, word_2: str) -> bool:
    """True iff word_1 and word_2 differ by exactly 1 jamo in exactly 1 syllable.

    Both words must consist entirely of Hangul syllable blocks and be the same
    length.
    """
    if len(word_1) != len(word_2) or word_1 == word_2:
        return False
    if not all(is_syllable(c) for c in word_1 + word_2):
        return False

    diff_count = 0
    for c1, c2 in zip(word_1, word_2):
        if c1 == c2:
            continue
        diff_count += 1
        if diff_count > 1:
            return False
        if jamo_distance(c1, c2) != 1:
            return False
    return diff_count == 1

# ---------------------------------------------------------------------------
# Load words from topik_words.csv
# ---------------------------------------------------------------------------
def load_topik_words(filepath, allowed_words=None, index_override=None):
    """Load words; optionally filter and override index for ranking.

    allowed_words  : dict or set of 단어 to keep (None = all).
    index_override : dict {word: {'index': rank, ...}} or {word: int} replacing
                     the TOPIK index.
    """
    words = []
    with open(filepath, encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        for row in reader:
            try:
                idx = int(row['Index'])
            except (ValueError, KeyError):
                continue
            word = row.get('단어', '').strip()
            if not word:
                continue
            if allowed_words is not None and word not in allowed_words:
                continue
            if index_override is not None:
                entry = index_override.get(word)
                if entry is not None:
                    idx = entry['index'] if isinstance(entry, dict) else entry
            words.append({
                'index': idx,
                '순위':  row.get('순위', ''),
                '단어':  word,
                '품사':  row.get('품사', ''),
                '풀이':  row.get('풀이', ''),
                '등급':  row.get('등급', '').strip(),
            })
    return words


# ---------------------------------------------------------------------------
# Load Anki word list  →  dict {word: anki_index}
# ---------------------------------------------------------------------------
def load_anki_words(filepath):
    """Return a dict {word: {'index': int, 'english': str}} from the Anki CSV.

    Tab-separated, no header:
      col 0 = row number
      col 1 = Korean word
      col 2 = English translation
    When the same word appears more than once the first (lowest) index wins.
    """
    words = {}
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            fields = line.rstrip('\n').split('\t')
            if len(fields) >= 2:
                try:
                    idx = int(fields[0].strip())
                except ValueError:
                    continue
                w = fields[1].strip()
                english = fields[2].strip() if len(fields) >= 3 else ''
                if w and w not in words:
                    words[w] = {'index': idx, 'english': english}
    return words


# ---------------------------------------------------------------------------
# Pair score  =  1 / (1/i1 + 1/i2)  — lower is better
# ---------------------------------------------------------------------------
def pair_score(w1, w2):
    return 1.0 / (1.0 / w1['index'] + 1.0 / w2['index'])


# ---------------------------------------------------------------------------
# Find all single-jamo-apart pairs
# ---------------------------------------------------------------------------
def find_pairs(words):
    # Deduplicate on 단어: keep the entry with the lowest index for each word.
    seen_words = {}
    for w in words:
        key = w['단어']
        if key not in seen_words or w['index'] < seen_words[key]['index']:
            seen_words[key] = w
    words = list(seen_words.values())

    pairs = []
    # Group by word length to avoid comparing across lengths
    by_length = {}
    for w in words:
        length = len(w['단어'])
        by_length.setdefault(length, []).append(w)

    for length, group in by_length.items():
        for w1, w2 in combinations(group, 2):
            if single_jamo_apart(w1['단어'], w2['단어']):
                pairs.append((w1, w2))

    # Sort by score ascending (most common pair first)
    pairs.sort(key=lambda p: pair_score(p[0], p[1]))
    return pairs


# ---------------------------------------------------------------------------
# Write output CSV  — simple format: row, score, korean_1, english_1, ...
# ---------------------------------------------------------------------------
HEADERS = ['Row', 'Score', 'Korean_1', 'English_1', 'Korean_2', 'English_2']

def write_pairs(pairs, filepath, anki_dict=None):
    """
    anki_dict : dict {word: {'index': int, 'english': str}} used for English
                lookup.  If None or a word is missing, English is left blank.
    """
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(HEADERS)
        for row_num, (w1, w2) in enumerate(pairs, 1):
            score = pair_score(w1, w2)
            def eng(w):
                if anki_dict is None:
                    return ''
                entry = anki_dict.get(w['단어'])
                return entry['english'] if isinstance(entry, dict) else ''
            writer.writerow([
                row_num, f'{score:.6f}',
                w1['단어'], eng(w1),
                w2['단어'], eng(w2),
            ])
    print(f'Written {len(pairs):,} pairs -> {filepath}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print('Loading Anki word list from {ANKI_FILE}...')
    anki_words = load_anki_words(ANKI_FILE)   # dict {word: {'index', 'english'}}
    # index_override expects {word: int} or {word: dict with 'index' key}
    print(f'  {len(anki_words):,} unique words in Anki deck.')

    print('Loading all TOPIK words…')
    all_words = load_topik_words(INPUT_FILE)
    print(f'  {len(all_words):,} words loaded.')
    print('Finding single-jamo pairs (all)…')
    pairs_all = find_pairs(all_words)
    write_pairs(pairs_all, os.path.join(OUTPUT_DIR, 'similar_pairs_all.csv'),
                anki_dict=anki_words)

    my_words = load_topik_words(INPUT_FILE, allowed_words=anki_words,
                                index_override=anki_words)
    print(f'  {len(my_words):,} matched in TOPIK vocab.')
    print('Finding single-jamo pairs (my words)…')
    pairs_my = find_pairs(my_words)
    write_pairs(pairs_my, os.path.join(OUTPUT_DIR, 'similar_pairs_my_words.csv'),
                anki_dict=anki_words)

    print('\nDone.')

I want to convert this csv to match this spec with python.@beautifulMention 

SPEC
```
ANKI IMPORT SPECIFICATION: KOREAN CHUNK RANDOMIZER
==================================================
File Format: TSV (Tab-Separated Values)
File Extension: .txt or .tsv
Text Encoding: UTF-8 (Required for Korean characters)
Delimiter: Tab (\t)

GENERAL RULES
-------------
1. Each row represents exactly one Anki note.
2. Columns are strictly separated by a single Tab character.
3. The chunk fields (Columns 3, 4, and 5) MUST use a pipe character (|) to separate individual items. 
4. The number of pipe-separated items in Columns 3, 4, and 5 must be exactly the same for a given row.

COLUMN DEFINITIONS (Left to Right)
----------------------------------

COLUMN 1: Word_Korean
- Description: The single target vocabulary word in Korean.
- Format: Plain text.
- Example: 사과

COLUMN 2: Word_English
- Description: The English translation of the target vocabulary word.
- Format: Plain text.
- Example: Apple

COLUMN 3: Chunks_Korean
- Description: A list of Korean sentences or phrases containing the target word.
- Format: Plain text. Multiple entries MUST be separated by a pipe character (|).
- Example: 사과를 먹어요|빨간 사과

COLUMN 4: Chunks_English
- Description: The English translations of the Korean chunks.
- Format: Plain text. MUST be separated by a pipe (|). 
- Example: I eat an apple|A red apple

COLUMN 5: Chunks_Audio
- Description: The Anki sound tags corresponding to each chunk.
- Format: Anki sound bracket format. MUST be separated by a pipe (|).
- Example: [sound:apple_chunk1.mp3]|[sound:apple_chunk2.mp3]

==================================================
EXAMPLE RAW DATA (Tabs used between columns)
==================================================
사과	Apple	*사과*를 먹어요|빨간 *사과*	I eat an *apple*|A red *apple*	[sound:apple1.mp3]|[sound:apple2.mp3]
학교	School	*학교*에 가요|큰 *학교*	I go to *school*|A big *school*	[sound:school1.mp3]|[sound:school2.mp3]
You are helping a Korean language learner enrich their vocabulary CSV.

For each entry, generate TWO short, natural Korean phrase chunks that show how the word is typically used in real life.  
Provide an English translation for each chunk.

Each chunk should:
- Be 2–5 words long (short, memorable, and natural).
- Represent very common, everyday usage by native speakers.
- Show typical collocations or expressions (noun phrases, verb phrases, etc.).
- Always use correct particles where relevant.
- The first of the two chunks should show the word close to its base or noun form to reinforce recognition.
- The second chunk may use more natural forms — you may conjugate, add particles, or make a noun into a verb or a verb into an adjective if that’s how it’s usually used.
- Avoid long sentences or rare/academic expressions.
- Focus on realistic, high-frequency usage — not literal translations.

All Korean examples must sound completely natural, as if written by a native speaker.  
자연스러운 한국어 표현을 사용하세요. 인공적이거나 어색한 문장은 피하세요.

Return the results in the following CSV format:

Index|Lesson|Unit|Dialogue|Korean|English|Hanja|Explanation|Korean Chunk 1|English Chunk 1|Korean Chunk 2|English Chunk 2

Example input:
Index|Lesson|Unit|Dialogue|Korean|English|Hanja|Explanation
361|12|1|Dialogue|안내원|guide|案內員|plan, inside, person
354|12|1|Dialogue|군데|a place||place
363|12|1|Dialogue|코스|course||course
364|12|1|Dialogue|넉넉하다|to be plentiful||ample
404|13|2|Dialogue|아깝다|to be a waste of||regrettable
384|13|1|Dialogue|의류|clothing|衣類|clothes, category

Example output:
Index|Lesson|Unit|Dialogue|Korean|English|Hanja|Explanation|Korean Chunk 1|English Chunk 1|Korean Chunk 2|English Chunk 2
361|12|1|Dialogue|안내원|guide|案內員|plan, inside, person|관광 안내원|tour guide|안내원을 찾다|to look for a guide
354|12|1|Dialogue|군데|a place||place|한 군데|one place|몇 군데|a few places
363|12|1|Dialogue|코스|course||course|여행 코스|travel course|코스를 돌다|to go around a course
364|12|1|Dialogue|넉넉하다|to be plentiful||ample|음식이 넉넉하다|there’s plenty of food|넉넉하게 준비했어요|I prepared generously
404|13|2|Dialogue|아깝다|to be a waste of||regrettable|시간이 아깝다|it’s a waste of time|아깝게 졌어요|we lost narrowly
384|13|1|Dialogue|의류|clothing|衣類|clothes, category|의류 매장|clothing store|의류를 정리하다|to organize clothes

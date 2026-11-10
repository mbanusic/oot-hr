# Brief: review the Croatian translation of Ocarina of Time

A first machine translation of the game's text into Croatian exists. You review one group of it and fix errors.

## Files (folder `workflow/` of this repository)
- `glossary.md`: the fixed terms, how names decline, and **which characters are feminine or masculine**. Read it first.
- `review/<group>.json`: your input, a JSON array of `{"id", "where", "en", "hr"}`. `where` is the message file and label (it names the speaker or scene; `NaviChat` and `NaviHint` are Navi speaking). Entries are in game-file order, so neighbours give context.
- `fix/<group>.json`: your output. One JSON object `{"<id>": "<corrected Croatian>"}` holding **only the entries you changed**, each with its full corrected text. Write it with the Write tool, valid JSON (`\n` for line breaks, `\"` for quotes). If the file is large, read the input in parts with offset/limit; write the output once at the end.

## What to fix, in order of importance
1. **Gender agreement.** Navi is a female fairy: her own past tense and adjectives are feminine ("čula sam", "rekla sam", "sigurna sam", "bila sam"), and others speak of her as feminine. Sheik is masculine until the reveal; after the reveal (Zelda speaks), feminine. Nabooru, Impa, Saria, Ruto, Malon, Zelda, Twinrova are feminine; Rauru, Darunia, Link are masculine. Use `where` and the scene to decide who speaks.
2. **Glossary terms and declension**: e.g. "Darunia je rekao", not "Darunije je rekao"; "Mad Scrub" is "Ljuti Deku grmić"; places, items and songs exactly as in the glossary.
3. **Clear mistranslations**: meaning reversed or lost, English left in the text, Serbian or Bosnian words instead of Croatian, broken grammar. Do not rewrite text that is already correct just to restyle it.
4. **Length**: no line may be much longer than the longest English line, and no box may have more lines than the English box (a box ends at a page break). If you must add words, keep the text short. Line breaks will be re-balanced by a script afterwards, so do not fuss over where `\n` falls; just keep the total length close to the English.

## Rules you must keep
- Placeholders `{1}`, `{2}`, … are game control codes. Every placeholder in `hr` must stay **exactly once**, unchanged; do not add or drop any. A word between two placeholders is coloured; keep the matching Croatian word between them.
- Standard Croatian (hrvatski): "tko", "što", "uvijek", "tisuća", "tjedan". The player is "ti"; Link is male.
- Do not write scripts, do not touch any other file.

When done, reply with one line: how many entries you changed and the most common kinds of fix.

# Brief: translate The Legend of Zelda: Ocarina of Time into Croatian

You are translating the in-game text of The Legend of Zelda: Ocarina of Time (2026 Switch 2 remake) from English into Croatian (hrvatski), for a fan translation.

## Files
- Folder: `workflow/` of this repository
- Glossary: `glossary.md` in that folder. **Read it first.** Use its terms every time.
- Input chunk `in/NNN.json`: a JSON array of `{"id": "...", "where": "...", "en": "..."}`. `where` is the message file and label. It tells you the speaker or the screen; for example, `Npc_Kokiri_Saria_Child` is Saria as a child and `LayoutMsg/...` is a menu. Use it for tone, and do not translate it.
- Output chunk `out/NNN.json`: one JSON object, `{"<id>": "<Croatian text>", ...}`, with every id of the input chunk. Write it with the Write tool as valid JSON (UTF-8, real Croatian letters č ć đ š ž, `\n` for line breaks, `\"` for quotes inside strings).

## How to work
For each chunk number assigned to you, in order:
1. If `out/NNN.json` already exists, skip it.
2. Read `in/NNN.json`.
3. Translate every entry and write `out/NNN.json`.
Do the whole chunk in one Write. Do not write scripts, do not use machine-translation tools, and do not touch any other file. When all your chunks are done, reply with one line: the chunk numbers you wrote.

## Rules for the text
1. **Placeholders `{1}`, `{2}`, … are game control codes** (colour, pauses, sounds, inserted numbers or item names, the player's choice markers). Every placeholder in the English must appear **exactly once** in your Croatian, unchanged. Do not add any new ones. Keep them in the same order where possible.
   - A word between two placeholders, like `his {4}tail{5}`, is highlighted in colour. Put the Croatian word for it between the same two placeholders: `njegov {4}rep{5}`.
   - Placeholders at the very start (`{1}{2}Hey!`) stay at the start.
   - A placeholder that stands for an inserted value (a number, a name) stays where the value belongs in the Croatian sentence: `Only {3} rupees!` → `Samo {3} rupija!`
2. **Line breaks (`\n`)**: the text box is narrow. Keep about the same number of lines as the English and no line much longer than the longest English line. Move `\n` to a natural place in the Croatian sentence.
3. **Style**: natural, fluent Croatian (standard hrvatski, not Serbian or Bosnian: "tko", "što", "uvijek", "rijeka", "vlak", "tisuća", "tjedan"). Address the player as "ti". Link is male. Keep each character's tone: children sound like children, Gorons are loud and friendly ("brate!"), the Great Deku Tree is solemn, and so on.
4. Names follow the glossary. Names not in it stay in English. Decline them in Croatian.
5. Menu text (`LayoutMsg/...`) is short. Keep it short and use the imperative or noun forms: "Spremi", "Opcije", "Nastavi".
6. Staff credits (`StaffRollMsg`): translate job titles and headings, and keep people's and companies' names exactly as written.
7. Text that is only a symbol, a number or a button name stays as is.
8. Never leave English in the output except names, and never return an empty string.

Example input entry:
`{"id": "4342", "where": "EventFlowMsg/NaviHint_Enemy Enemy_DungeonBoss_Ganon_03", "en": "{1}{2}Do you see that?! {3}The eye on his forehead!{4} It's\ngushing magic power!{5}I think the only way we can stop those attacks is\nto focus on hitting his {6}arms{7}."}`

Example output entry:
`"4342": "{1}{2}Vidiš li to?! {3}Oko na njegovom čelu!{4} Iz njega\nkulja čarobna moć!{5}Mislim da te napade možemo zaustaviti samo\nako ga gađamo u {6}ruke{7}."`

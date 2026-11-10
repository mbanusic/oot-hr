# Ocarina of Time: hrvatski prijevod

A Croatian fan translation of the in-game text of The Legend of Zelda: Ocarina of Time (the Switch 2 release, title `0400486024DEC000`, version 1.1.1). It is made for playing the game through [nxnative](https://github.com/seedds/nxnative) on a Mac, iPhone or iPad. The game files are not replaced: nxnative swaps the translated text in at runtime.

The repository holds the translation and the tools, not the game. You need your own copy of the game.

## What is translated

All 21,138 texts in the game's message archive, including dialogue, cutscene subtitles, menus, item descriptions, the story log, hints and the credit roles. 518 of them hold only control codes and have no text, so 20,620 entries are translated.

This is a first, machine-made translation (Claude), reviewed for character genders, terms, line length and grammar. It has not yet been read through by a native speaker, so expect stiff phrasing in places. Corrections are welcome (see [Editing the translation](#editing-the-translation)).

Known limits:
- The game runs with its English language setting, so plural words built in by the game (such as "rupija") follow the English rule: one form for 1 and another for every other number. The Croatian forms are chosen so that this reads correctly for 1 and for 5 or more; with 2–4 you see, for example, "3 rupija".
- Text in images and textures (logos, some menu graphics) stays in English.
- The decorative font `Nin-ZeldaGlyphs-v3` has no č, Č, đ or Đ. Dialogue, subtitles and menus use the normal fonts, which have every Croatian letter.

## Files

| File | What it is |
|---|---|
| `hr.json` | The translation: `{"<message file>|<label>": "Croatian text"}`. Game control codes are written `{{g.t:hex}}` and are kept as they are. |
| `mals_po.py` | Builds the translated message archive from your game's files, and converts the translation to and from a `.po` file for editing. |
| `workflow/` | How the translation was made: the glossary, the briefs for the translating and reviewing agents, and the scripts that split, merge, re-wrap and check the text. |

## Requirements

- Python 3.14 or newer (for its built-in zstd: `brew install python@3.14`), or Python 3.13 with `pip install backports.zstd`.
- The game's RomFS from your own copy, unpacked, or at least these two parts of it:
  - `Pack/ZsDic.pack.zs`
  - `Mals/` (the `*.Product.*.sarc.zs` message archives)

  Put them in one folder, called `orig/` below, with the same layout as in the RomFS.

## Build the translated text

```sh
python3.14 mals_po.py selftest orig EUen        # optional: checks that the tool reads and rewrites your copy exactly
python3.14 mals_po.py build orig EUen hr.json overlay --as USen --as EUen
```

This writes `overlay/Mals/USen.Product.110.sarc.zs` and `overlay/Mals/EUen.Product.110.sarc.zs`. Both are the same Croatian archive, under the two English names, so it is used whether the game runs as American or British English.

## Build it in NX2Apple

`nx2apple-mod.json` lets the [NX2Apple](https://github.com/LNPANDY/NX2Apple) launcher build the translation from your game for you (LNPANDY/NX2Apple#1133, not in a release yet). Put this repository's folder in the game's mods folder (Launch options › Mods › Open mods folder), click Build, then switch the mod on.

## Play it

nxnative reads replacement files from the folder named by `DM_ROMFS_OVERLAY`. Point it at the `overlay` folder:

- **Mac:** add this line to `~/Library/Application Support/nxnative/0400486024DEC000/env.txt` (create the file if it does not exist), then start the game:
  ```
  DM_ROMFS_OVERLAY=/full/path/to/overlay
  ```
- **iPhone / iPad:** copy the `overlay` folder into the app's Documents folder (Files app, or Finder with the device connected), and add this line to `Documents/env.txt`:
  ```
  DM_ROMFS_OVERLAY=overlay
  ```
  A relative path is read from the Documents folder.

Keep the game's language at English (the default). To go back to English text, remove the line.

## Editing the translation

The easiest way to edit is in a `.po` editor such as [Poedit](https://poedit.net), which shows each English text next to its Croatian one:

```sh
python3.14 mals_po.py export orig EUen hr.po --tr hr.json     # English from your copy + the current Croatian
# edit hr.po in Poedit
python3.14 mals_po.py tojson hr.po hr.json                    # save the Croatian back
python3.14 mals_po.py build orig EUen hr.json overlay --as USen --as EUen
```

`hr.po` contains the game's English text, so it is not part of the repository; only `hr.json` is.

Rules for the text (the full list is in [`workflow/BRIEF.md`](workflow/BRIEF.md) and [`workflow/glossary.md`](workflow/glossary.md)):
- Keep every control code (`{{0.3:0000}}`, `{{5.1}}`, …) exactly once and unchanged. `{{0.3:0000}}` … `{{0.3:ffff}}` colours the words between them; `{{0.4}}` starts a new text box; `{{2.…}}` inserts a value, such as a number or a name.
- A dialogue box holds 3 lines of about 52–60 characters. Use `\n` for a line break.
- An English text that is only an article ("the", "a") is translated as `{{empty}}`, which makes it empty in the game.
- Use the terms and character genders from the glossary: for example, Navi is female and Sheik is male.

`build` prints a warning when the control codes of a translated text differ from the English. The only expected warnings are for the `{{201.6:…}}` codes, which carry the Croatian plural words.

## How it was made

1. `mals_po.py export` produced a `.po` file of the 21,138 English texts.
2. `workflow/chunks.py prepare` replaced the control codes with `{1}`, `{2}`, …, merged the 17,971 unique texts and split them into 156 chunks. Twelve Claude Haiku agents translated them following `BRIEF.md` and `glossary.md`. `chunks.py merge` checked every placeholder and wrote the result back.
3. `workflow/rewrap.py` re-broke the lines to fit the text boxes, since the English line width is the limit.
4. Six Claude Sonnet agents reviewed the text following `REVIEW.md`, mostly fixing character genders, name declension, glossary terms and grammar; `applyfix.py` applied their 412 fixes after checking the placeholders.
5. `plurals.py` put Croatian plural forms into the `{{201.6}}` codes, and a few over-long boxes were shortened by hand.
6. The result was checked in the game on a Mac, from a new game up to Link's first steps: the title menu, the opening cutscenes, Navi's introduction and name card, and the control hints. The dialogue boxes of later characters have not been seen yet.

## Legal

This is an unofficial fan project, not affiliated with or endorsed by Nintendo. *The Legend of Zelda* and *Ocarina of Time* are trademarks of Nintendo. The repository contains only the Croatian translation and tools, not the game or its English text.

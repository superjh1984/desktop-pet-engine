# Cursor theme workflow

Use cursor themes only when the user explicitly wants to change the macOS
system cursor as part of the desktop-pet experience.

## Distribution boundary

- Keep cursor control code separate from cursor artwork.
- Public repositories may include only `.cape` files the user created or has
  permission to redistribute.
- Never move restricted character, person, team, brand, or internal demo cursor
  artwork into the public template.
- Mousecape is an optional external dependency. Do not bundle, install, copy, or
  modify it on the user's behalf.
- Mousecape's upstream project says that it uses private CoreGraphics APIs and
  restricts use or modification to personal, non-commercial purposes. Preserve
  this disclosure and direct users to the upstream license.

## Configuration

1. Copy `cursor_themes.example.json` to the ignored
   `cursor_themes.json`.
2. Put authorized `.cape` files in the ignored `CursorThemes/` directory.
3. For every entry, set:
   - a unique safe theme `id`;
   - English and Simplified Chinese titles;
   - the `.cape` filename;
   - the exact `Identifier` stored inside the cape;
   - optional `PetAction` raw values that should trigger the theme.
4. Run `scripts/check_demo.sh`.

The engine rejects path traversal, unsafe or duplicate identifiers, missing
files, unknown actions, and cape identifiers that do not match the manifest.

For a rights-safe local demonstration, run
`scripts/generate_demo_cursor_themes.py`. It creates two original Blob cursor
themes using only Python's standard library. Its output is ignored by Git.

## Runtime behavior

- The selected base theme is stored in `UserDefaults`.
- When action-following is enabled, a matching action theme temporarily
  replaces the base theme.
- Returning to idle restores the base theme.
- Selecting System Default asks Mousecape's `mousecloak` executable to reset
  the cursor.
- Missing Mousecape or invalid configuration should show a recoverable
  bilingual alert and must not prevent the pet from launching.

## Validation

- Run the generated app with `--cursor-self-test`.
- Confirm Mousecape itself is absent from the app bundle.
- Confirm the app restores the selected base theme after action playback,
  hiding the pet, and quitting.
- Test both a Mac with Mousecape installed and one without it.

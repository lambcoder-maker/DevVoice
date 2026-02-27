"""Post-processing pipeline: voice commands and word substitutions.

Three layers applied in order after each transcription:
  1. detect_control_command() — if the whole utterance IS a command, return its
     action key so the caller can execute it without typing anything.
  2. apply_word_map()          — user-defined spoken→typed substitutions.
  3. apply_punctuation_commands() — spoken punctuation / formatting words
                                    replaced with the actual symbols.
"""

import re


# ---------------------------------------------------------------------------
# Spoken punctuation → symbol  (applied inline, whole-word, case-insensitive)
# ---------------------------------------------------------------------------
_PUNCTUATION_COMMANDS = [
    (r'\bcomma\b',                   ','),
    (r'\bperiod\b',                  '.'),
    (r'\bfull stop\b',               '.'),
    (r'\bquestion mark\b',           '?'),
    (r'\bexclamation mark\b',        '!'),
    (r'\bexclamation point\b',       '!'),
    (r'\bcolon\b',                   ':'),
    (r'\bsemicolon\b',               ';'),
    (r'\bnew line\b',                '\n'),
    (r'\bnewline\b',                 '\n'),
    (r'\bnew paragraph\b',           '\n\n'),
    (r'\bopen paren(?:thesis)?\b',   '('),
    (r'\bclose paren(?:thesis)?\b',  ')'),
    (r'\bopen bracket\b',            '['),
    (r'\bclose bracket\b',           ']'),
    (r'\bopen brace\b',              '{'),
    (r'\bclose brace\b',             '}'),
    (r'\bdash\b',                    '-'),
    (r'\bem dash\b',                 '—'),
    (r'\bellipsis\b',                '…'),
    (r'\bdot\b',                     '.'),
    (r'\bslash\b',                   '/'),
    (r'\bbackslash\b',               '\\'),
    (r'\bat sign\b',                 '@'),
    (r'\bhash\b',                    '#'),
    (r'\bpercent(?:\s+sign)?\b',     '%'),
    (r'\bampersand\b',               '&'),
    (r'\basterisk\b',                '*'),
    (r'\bplus\b',                    '+'),
    (r'\bequals(?:\s+sign)?\b',      '='),
    (r'\bgreater than\b',            '>'),
    (r'\bless than\b',               '<'),
    (r'\bpipe\b',                    '|'),
    (r'\btilde\b',                   '~'),
    (r'\bbacktick\b',                '`'),
    (r'\bquote\b',                   '"'),
    (r'\bsingle quote\b',            "'"),
    (r'\btab\b',                     '\t'),
]

# ---------------------------------------------------------------------------
# Standalone control commands
# The ENTIRE transcription (stripped, lowercase) must match one of these.
# Value is the action key passed back to app.py.
# ---------------------------------------------------------------------------
_CONTROL_COMMANDS: dict[str, str] = {
    'scratch that':     'undo',
    'delete that':      'undo',
    'undo that':        'undo',
    'delete last':      'undo',
    'select all':       'select_all',
    'copy that':        'copy',
    'copy all':         'copy',
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_control_command(text: str) -> str | None:
    """Return an action key if the whole utterance is a control command.

    Returns one of: 'undo', 'select_all', 'copy', or None.
    """
    normalized = text.strip().rstrip('.!?,').lower()
    return _CONTROL_COMMANDS.get(normalized)


def apply_word_map(text: str, word_map: dict) -> str:
    """Apply user-defined spoken→typed substitutions (whole-word, case-insensitive)."""
    for spoken, typed in word_map.items():
        if not spoken:
            continue
        pattern = r'\b' + re.escape(spoken) + r'\b'
        text = re.sub(pattern, typed, text, flags=re.IGNORECASE)
    return text


def apply_punctuation_commands(text: str) -> str:
    """Replace spoken punctuation / formatting words with their symbols."""
    for pattern, replacement in _PUNCTUATION_COMMANDS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Remove spurious space before punctuation: "hello , world" → "hello, world"
    text = re.sub(r'\s+([,\.!?:;])', r'\1', text)

    return text.strip()


def process(text: str, word_map: dict = None, punctuation_enabled: bool = True) -> tuple[str, str | None]:
    """Run the full post-processing pipeline on a raw transcription.

    Returns:
        (processed_text, control_action)
        If control_action is not None the caller should execute that action
        instead of typing processed_text.
    """
    command = detect_control_command(text)
    if command:
        return ('', command)

    result = text
    if word_map:
        result = apply_word_map(result, word_map)
    if punctuation_enabled:
        result = apply_punctuation_commands(result)

    return (result, None)

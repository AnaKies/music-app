STEP_TO_SEMITONE = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def parse_note_name_to_midi(note_name: str) -> int:
    candidate = note_name.strip().replace("♭", "b").replace("♯", "#")
    if len(candidate) < 2:
        raise ValueError("invalid_target_range")

    step_symbol = candidate[0].upper()
    if step_symbol not in {"A", "B", "C", "D", "E", "F", "G", "H"}:
        raise ValueError("invalid_target_range")

    index = 1
    alter = 0
    step = "B" if step_symbol == "H" else step_symbol

    if index < len(candidate):
        accidental = candidate[index]
        if accidental == "#":
            alter = 1
            index += 1
        elif accidental in {"b", "B"}:
            alter = -1
            index += 1

    octave_text = candidate[index:].strip()
    if not octave_text or not octave_text.lstrip("-").isdigit():
        raise ValueError("invalid_target_range")

    octave = int(octave_text)
    return (octave + 1) * 12 + STEP_TO_SEMITONE[step] + alter


def normalize_note_bounds(min_note: str, max_note: str) -> tuple[str, str]:
    min_midi = parse_note_name_to_midi(min_note)
    max_midi = parse_note_name_to_midi(max_note)
    if min_midi <= max_midi:
        return min_note, max_note
    return max_note, min_note

from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from backend.api.schemas.transformations import TransformationWarning, TransformationWarningSeverity
from backend.services.shared.musicxml import serialize_musicxml_document
from backend.services.shared.note_ranges import parse_note_name_to_midi
STEP_TO_SEMITONE = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

SEMITONE_TO_PITCH = {
    0: ("C", 0),
    1: ("C", 1),
    2: ("D", 0),
    3: ("D", 1),
    4: ("E", 0),
    5: ("F", 0),
    6: ("F", 1),
    7: ("G", 0),
    8: ("G", 1),
    9: ("A", 0),
    10: ("A", 1),
    11: ("B", 0),
}


@dataclass
class TransformationEngineResult:
    transformed_musicxml: str
    semitone_shift: int
    warnings: List[TransformationWarning]


def transform_musicxml_to_target_range(
    musicxml: str,
    target_range_min: str,
    target_range_max: str,
) -> TransformationEngineResult:
    root = ElementTree.fromstring(musicxml)
    note_nodes = [note for note in root.findall(".//{*}note") if note.find("{*}pitch") is not None]
    if not note_nodes:
        raise ValueError("incomplete_source_score")

    source_midis = []
    for note in note_nodes:
        midi = _read_note_midi(note)
        if midi is not None:
            source_midis.append(midi)

    if not source_midis:
        raise ValueError("incomplete_source_score")

    target_min_midi = parse_note_name_to_midi(target_range_min)
    target_max_midi = parse_note_name_to_midi(target_range_max)
    if target_min_midi > target_max_midi:
        target_min_midi, target_max_midi = target_max_midi, target_min_midi

    source_min = min(source_midis)
    source_max = max(source_midis)
    lower_bound = target_min_midi - source_min
    upper_bound = target_max_midi - source_max
    semitone_shift = _choose_semitone_shift(lower_bound, upper_bound)

    warnings: List[TransformationWarning] = []
    if lower_bound > upper_bound:
        warnings.append(
            TransformationWarning(
                code="range_overflow",
                severity=TransformationWarningSeverity.WARNING,
                message="The selected range is narrower than the score span. The transformation used the closest deterministic shift and some notes may remain out of range.",
            )
        )

    for note in note_nodes:
        midi = _read_note_midi(note)
        if midi is None:
            continue
        _write_note_midi(note, midi + semitone_shift)

    transformed_midis = [midi + semitone_shift for midi in source_midis]
    if min(transformed_midis) < target_min_midi or max(transformed_midis) > target_max_midi:
        warnings.append(
            TransformationWarning(
                code="range_boundary_violation",
                severity=TransformationWarningSeverity.WARNING,
                message="The transformed score still exceeds the selected range boundaries because no clean interval-preserving shift could fully fit the score.",
            )
        )

    transformed_musicxml = serialize_musicxml_document(root)
    return TransformationEngineResult(
        transformed_musicxml=transformed_musicxml,
        semitone_shift=semitone_shift,
        warnings=warnings,
    )


def _choose_semitone_shift(lower_bound: int, upper_bound: int) -> int:
    if lower_bound <= upper_bound:
        if 0 < lower_bound:
            return lower_bound
        if 0 > upper_bound:
            return upper_bound
        return 0

    if abs(lower_bound) < abs(upper_bound):
        return lower_bound
    return upper_bound


def _read_note_midi(note: ElementTree.Element) -> Optional[int]:
    pitch = note.find("{*}pitch")
    if pitch is None:
        return None

    step_node = pitch.find("{*}step")
    octave_node = pitch.find("{*}octave")
    alter_node = pitch.find("{*}alter")
    if step_node is None or octave_node is None or not step_node.text or not octave_node.text:
        return None

    step = step_node.text.strip().upper()
    octave = int(octave_node.text.strip())
    alter = int(alter_node.text.strip()) if alter_node is not None and alter_node.text else 0
    return (octave + 1) * 12 + STEP_TO_SEMITONE[step] + alter


def _write_note_midi(note: ElementTree.Element, midi_value: int) -> None:
    pitch = note.find("{*}pitch")
    if pitch is None:
        return

    step_node = pitch.find("{*}step")
    octave_node = pitch.find("{*}octave")
    alter_node = pitch.find("{*}alter")
    if step_node is None or octave_node is None:
        return

    octave = (midi_value // 12) - 1
    pitch_class = midi_value % 12
    step, alter = SEMITONE_TO_PITCH[pitch_class]
    step_node.text = step
    octave_node.text = str(octave)

    if alter == 0:
        if alter_node is not None:
            pitch.remove(alter_node)
    else:
        if alter_node is None:
            alter_node = ElementTree.SubElement(pitch, "alter")
        alter_node.text = str(alter)

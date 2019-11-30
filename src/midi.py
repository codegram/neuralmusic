from typing import Optional

from music21 import converter, instrument, note, chord
from music21.midi import MidiException
import pandas as pd


def parse_midi_file(file: str) -> (Optional[pd.DataFrame], int):
    """
    Attempts to parse a midi file into a Dataframe. Returns a Dataframe or None, together with the number of notes processed.
    """
    try:
        midi = converter.parse(file)
        notes_to_parse = None
        parts = instrument.partitionByInstrument(midi)
        notes = []
        if parts:  # file has instrument parts
            notes_to_parse = parts.parts[0].recurse()
        else:  # file has notes in a flat structure
            notes_to_parse = midi.flat.notes
        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append(
                    (
                        str(element.pitch),
                        float(element.duration.quarterLength),
                        element.volume.velocity,
                    )
                )
            elif isinstance(element, chord.Chord):
                notes.append(
                    (
                        ".".join(str(n) for n in element.normalOrder),
                        float(element.duration.quarterLength),
                        element.volume.velocity,
                    )
                )
        df = pd.DataFrame.from_dict(
            {
                "pitches": [[[pitch for (pitch, duration, velocity) in notes]]],
                "durations": [[[duration for (pitch, duration, velocity) in notes]]],
                "velocities": [[[velocity for (pitch, duration, velocity) in notes]]],
            }
        )
        return (df, len(notes))
    except MidiException:
        return (None, 0)
    except IndexError:
        return (None, 0)

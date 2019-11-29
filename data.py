from fastprogress import progress_bar
from pathlib import Path
from music21 import converter, instrument, note, chord
from music21.midi import MidiException
import pandas as pd

from fastparquet import write

def load_song(infile, outfile, append=False):
    try:
        midi = converter.parse(infile)
        notes_to_parse = None
        parts = instrument.partitionByInstrument(midi)
        notes = []
        if parts:  # file has instrument parts
            notes_to_parse = parts.parts[0].recurse()
        else:  # file has notes in a flat structure
            notes_to_parse = midi.flat.notes
        for element in notes_to_parse:
            if isinstance(element, note.Note):
                notes.append((str(element.pitch), element.duration.quarterLength))
            elif isinstance(element, chord.Chord):
                notes.append(
                    (
                        ".".join(str(n) for n in element.normalOrder),
                        element.duration.quarterLength,
                    )
                )
        new_df = pd.DataFrame.from_dict(
            {
                "pitches": [
                    [" ".join([pitch for (pitch, duration) in notes])]
                ],
                "durations": [
                    [" ".join([str(duration) for (pitch, duration) in notes])]
                ],
            }
        )
        write(outfile, new_df, append=append)
        return len(notes)
    except MidiException:
        return None

def load_songs(path, glob, out):
    midis = list(Path(path).glob(glob))
    note_count = 0
    songs = 0
    bar = progress_bar(range(len(midis)))
    for i in bar:
        file = midis[i]
        if i % 100 == 0:
            print(f"{i} songs, {note_count} notes")
        bar.comment = f"{note_count} notes"
        notes = load_song(file, out, append=i!=0)
        if notes is not None:
            songs += 1
            note_count += notes
    print(f"Total: {songs}, {note_count} notes")

load_songs("./data/", glob="raw/**/*.mid", out='data.parq')
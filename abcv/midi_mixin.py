from abcv.midiplayer import MidiPlayer

class MidiMixin(object):
    def __init__(self, port_name=None):
        self.midi = MidiPlayer(port_name)
        self.paused = False

    def toggle_play(self):
        if self.midi.playing:
            if self.paused:
                self.midi.unpause()
                self.paused = False
            else:
                self.midi.pause()
                self.paused = True
        else:
            self.midi.play()
            self.paused = False

    def restart(self):
        self.midi.stop()
        self.paused = False

    def load_midi(self, midi_file):
        self.midi.load(midi_file)


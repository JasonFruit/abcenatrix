import time
from threading import Thread

import mido

class MidiPlayer(object):
    def __init__(self):
        self.port_name = mido.get_output_names()[1]
        self._cur_time = 0
        self._filename = ""
        self._file = None
        self._playing = False
        self._paused = False
        
    @property
    def file(self):
        return self._filename

    @file.setter
    def file(self, new_file):
        self._filename = new_file
        self._file = mido.MidiFile(new_file)

    def load(self, midi_fn):
        self.file = midi_fn

    @property
    def duration(self):
        return self._file.length * 1000.

    @property
    def current_time(self):
        return self._cur_time

    @property
    def remaining_time(self):
        if self.current_time > self.duration:
            return 0
        else:
            return self.duration - self.current_time

    def play(self, midi_fn=None):
        if midi_fn:
            self.load(midi_fn)

        def do_play():
            port = mido.open_output(self.port_name)
            self._playing = True
            self._paused = False

            for msg in self._file.play():

                while self._paused:
                    port.reset()    # stop sounds
                    time.sleep(0.3)
                    if not self._playing:
                        break

                if not self._playing:
                    break

                self._cur_time += msg.time * 1000
                port.send(msg)

            self._playing = False
            self._paused = False

        t = Thread(target=do_play)
        t.daemon = True

        t.start()

    @property
    def playing(self):
        return self._playing

    def pause(self):
        self._paused = True

    def unpause(self):
        self._paused = False

    def stop(self):
        self._playing = False

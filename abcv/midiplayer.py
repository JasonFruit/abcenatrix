import time
from threading import Thread

import mido

class MidiPlayer(object):
    def __init__(self):

        # choose the first open port, for now
        try:
            self.port_name = self.ports[0]
        except IndexError:
            self.port_name = ""
            
        self._cur_time = 0
        self._filename = ""
        self._file = None
        self._playing = False
        self._paused = False
        self._scale = 1.0
        self._message_index = 0

    @property
    def ports(self):
        return mido.get_output_names()
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

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, new):
        self._scale = float(new)

    def play(self, midi_fn=None, resume=False):
        if midi_fn:
            self.load(midi_fn)

        def do_play():
            port = mido.open_output(self.port_name)
            self._playing = True
            self._paused = False


            # if you're not resuming, start from the beginning
            if not resume:
                start_index = 0
            else:
                start_index = self._message_index

            messages = [msg for msg in self._file]
            for self._message_index in range(start_index, len(messages)):

                if self._paused or not self._playing:
                    port.reset()
                    return
                
                msg = messages[self._message_index]
                
                time.sleep(msg.time / self._scale)
                
                if not msg.is_meta:
                    port.send(msg)
                    self._cur_time += msg.time * 1000

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
        if self._paused:
            self.play(resume=True)

    def stop(self):
        self._playing = False

import pygame
from mido import MidiFile


class MidiPlayer(object):
    def __init__(self):
        pygame.init()
        self.mido_file = None
    def load(self, midi_fn):
        self.filename = midi_fn
        pygame.mixer.music.load(midi_fn)
        self.mido_file = MidiFile(midi_fn)
    @property
    def duration(self):
        return self.mido_file.length * 1000
    @property
    def current_time(self):
        time =  pygame.mixer.music.get_pos()
        if time < 0:
            return 0.
        else:
            return float(time)
    @property
    def remaining_time(self):
        return self.duration - self.current_time
    def play(self, midi_fn=None):
        if midi_fn:
            self.load(midi_fn)
        pygame.mixer.music.play()
    @property
    def playing(self):
        return pygame.mixer.music.get_busy()
    def pause(self):
        pygame.mixer.music.pause()
    def unpause(self):
        pygame.mixer.music.unpause()
    def stop(self):
        if self.playing:
            pygame.mixer.music.stop()
            # it seems like the only way to get it to reset properly
            # is to reload the file
            self.load(self.filename)

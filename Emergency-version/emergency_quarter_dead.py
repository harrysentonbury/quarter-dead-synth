#!/usr/bin/env python3

import numpy as np
import sounddevice as sd
import threading
import time
import tkinter as tk
from tkinter import messagebox


def on_closing():
    if messagebox.askokcancel("Quit?", "Do You Want To Quit"):
        master.destroy()
        global flag
        flag = False


def play_it(event):
    global sound
    sound = key_notes.get(event.char)


def stop_it():
    master.destroy()
    global flag
    flag = False


def do_it(place_holder=0):
    def sine_wave(f, detune=0.0):
        y = np.sin((f + detune) * x + ramp_0 *
                   np.sin(((f + detune) * 0.5) * x + (np.sin(((f + detune) * fm) * x) * 0.5)))
        return y

    def triangle(f, detune=0.0):
        y = 2 / np.pi * np.arcsin(np.sin((f + detune) * x + ramp_0 *
                                         np.sin(((f + detune) * 0.5) * x + (np.sin(((f + detune) * fm) * x) * 0.5))))
        return y * 0.8

    fm = 0.25
    freq3 = 440.0
    freq5 = float(scale_freq5.get())
    duration = float(scale_duration.get())
    freq1 = float(scale_f1.get())
    ramp_amount = float(scale_ramp.get())
    roll_amount = int(scale_roll.get())
    st = float(scale_st.get())
    tm = st * 1.2
    sm = 1 - st

    x = np.linspace(0, 2 * np.pi * duration,
                    int(duration * sample_rate))
    ramp_0 = np.logspace(1, 0, np.size(x), base=10) * ramp_amount

    notes = []
    for i in range(-5, 10):
        factor = (2**(i / 12.0))
        waveform_mod = (sine_wave(freq1 * factor) * sm) + \
            (triangle(freq3 * factor, freq5) * tm)
        waveform = (sine_wave(freq1 * factor) * sm) + \
            (triangle(freq3 * factor) * tm)
        waveform_detune = (sine_wave(freq1 * factor, freq5)
                           * sm) + (triangle(freq3 * factor) * tm)

        waveform = ((waveform + waveform_detune) *
                    (waveform_mod / 2 + 0.5)) * 0.1

        leftover = np.size(waveform) // blocksize != 0
        if leftover != 0:
            extra = np.zeros(blocksize - leftover)
            waveform = np.concatenate((waveform, extra))

        waveform[-fade_amount:] *= fade
        waveform2 = np.roll(waveform, roll_amount, axis=None)
        waveform3 = np.vstack((waveform2, waveform)).T
        notes.append(waveform3)

    global key_notes
    key_notes = dict(zip(keys, notes))
    return key_notes


def stream_func():
    def callback(outdata, frames, time, status):
        try:
            data = next(block)
            if flag == False:
                raise sd.CallbackStop
            else:
                outdata[:, :] = data
        except ValueError:
            outdata[:, :] = np.zeros((blocksize, 2))

    stream = sd.OutputStream(channels=2, callback=callback, blocksize=blocksize,
                             samplerate=sample_rate)
    with stream:
        while flag == True:
            time.sleep(0.5)
        else:
            stream.__exit__()


def gen():
    global sound
    while True:
        slice = sound[:blocksize, :]
        yield slice
        sound = sound[blocksize:, :]


def binders(la):
    master.bind(f"<{la}>", play_it)


try:
    keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
            'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    sample_rate = 48000
    blocksize = 256
    fade_amount = 6000
    flag = True
    sound = np.zeros((blocksize, 2))
    block = gen()
    fade = np.linspace(1, 0, fade_amount)
    stream_thread = threading.Thread(target=stream_func)
    stream_thread.start()

    master = tk.Tk()
    master.geometry('700x500')
    master.configure(padx=20, pady=20)
    master.title("1/4 Dead Emergency")

    for key in keys:
        binders(f'{key}')
    master.bind("<ButtonRelease-1>", do_it)

    duration_label = tk.Label(master, text='Duration')
    freq5_label = tk.Label(master, text='Detune')
    f1_label = tk.Label(master, text='Sine Octave')
    ramp_label = tk.Label(master, text='Ramp')
    roll_label = tk.Label(master, text='Delay')
    sm_label = tk.Label(master, text='Sine')
    tm_label = tk.Label(master, text='Triangle')

    scale_duration = tk.Scale(master, from_=0.2, to=3.0, resolution=0.2,
                              orient=tk.HORIZONTAL, length=200)
    scale_freq5 = tk.Scale(master, from_=0.0, to=13.0,
                           resolution=0.2, orient=tk.HORIZONTAL, length=200)
    scale_f1 = tk.Scale(master, from_=220, to=440,
                        resolution=220, orient=tk.HORIZONTAL, length=50)
    scale_ramp = tk.Scale(master, from_=0.0, to=2.0,
                          resolution=0.01, orient=tk.HORIZONTAL, length=200)
    scale_roll = tk.Scale(master, from_=0, to=4000,
                          resolution=50, orient=tk.HORIZONTAL, length=200)
    scale_st = tk.Scale(master, from_=0.0, to=1.0,
                        resolution=0.005, orient=tk.HORIZONTAL, length=200, showvalue=0)

    close_button = tk.Button(master, text='Close', width=7, command=stop_it)

    scale_duration.set(1.0)
    scale_freq5.set(2.2)
    scale_f1.set(440)
    scale_ramp.set(0.25)
    scale_roll.set(600)

    duration_label.grid(row=0, column=0)
    freq5_label.grid(row=1, column=0)
    f1_label.grid(row=2, column=0)
    ramp_label.grid(row=3, column=0)
    roll_label.grid(row=4, column=0)
    sm_label.grid(row=5, column=0)
    tm_label.grid(row=5, column=2, sticky='w')

    scale_duration.grid(row=0, column=1)
    scale_freq5.grid(row=1, column=1)
    scale_f1.grid(row=2, column=1, sticky='w')
    scale_ramp.grid(row=3, column=1)
    scale_roll.grid(row=4, column=1)
    scale_st.grid(row=5, column=1, pady=20)
    close_button.grid(row=6, column=2, padx=20)

    key_notes = do_it()
    master.protocol("WM_DELETE_WINDOW", on_closing)
    master.mainloop()
except KeyboardInterrupt:
    flag = False
    print(' The End')
except Exception as e:
    flag = False
    print(f'{type(e).__name__}: {str(e)}')

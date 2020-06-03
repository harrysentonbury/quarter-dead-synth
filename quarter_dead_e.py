#!/usr/bin/env python3

import numpy as np
import simpleaudio as sa
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk


def play_it(event):
    if stop_flag.get() is False:
        sa.stop_all()
    play_obj = sa.play_buffer(key_notes.get(event.char), 2, 2, sample_rate)


def stop_it():
    sa.stop_all()


def do_it(place_holder=0):

    def wave_maker(a):
        factor = (2**(a / 12.0))
        waveform_mod = (sine_wave(freq1 * factor) * sm) + \
            (triangle(freq3 * factor, freq5) * tm)
        waveform = (sine_wave(freq1 * factor) * sm) + \
            (triangle(freq3 * factor) * tm)
        waveform_detune = (sine_wave(freq1 * factor, freq5)
                           * sm) + (triangle(freq3 * factor) * tm)

        waveform = ((waveform + waveform_detune) *
                    (waveform_mod / 2 + 0.5)) * 0.1

        waveform[-fade_amount:] *= fade
        waveform = np.int16(waveform * 32767)
        waveform2 = np.roll(waveform, roll_amount, axis=None)
        waveform3 = np.vstack((waveform2, waveform)).T
        waveform3 = (waveform3.copy(order='C'))
        return waveform3

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

    x = np.linspace(0, 2 * np.pi * duration, int(duration * sample_rate))
    ramp_0 = np.logspace(1, 0, np.size(x), base=10) * ramp_amount

    notes = []
    with ThreadPoolExecutor() as executor:
        notes = list(executor.map(wave_maker, range(-5, 10)))

    global key_notes
    key_notes = dict(zip(keys, notes))
    return key_notes


def toggle_flag():
    sa.stop_all()
    stop_flag.set(not stop_flag.get())
    if stop_flag.get() is True:
        toggle_button.config(bg="#728C00", fg="white", text="Poly")
    else:
        toggle_button.config(bg="#000000", fg="white", text="Mono")


def binders(la):
    master.bind(f"<{la}>", play_it)


try:
    keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
            'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    sample_rate = 48000
    fade_amount = 8000
    fade = np.linspace(1, 0, fade_amount)

    master = tk.Tk()
    master.geometry('700x500')
    master.configure(padx=20, pady=20)
    master.title("1/4 Dead in E4")

    stop_flag = tk.BooleanVar()
    stop_flag.set(False)

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

    scale_duration = tk.Scale(master, from_=0.2, to=5.0, resolution=0.2,
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

    stop_it_button = tk.Button(master, text='Stop', width=7, command=stop_it)
    toggle_button = tk.Button(master, text='Mono',
                              bg="#000000", fg="white", width=7, command=toggle_flag)
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
    stop_it_button.grid(row=0, column=2, padx=20)
    toggle_button.grid(row=2, column=2, padx=20)

    key_notes = do_it()
    master.mainloop()
except KeyboardInterrupt:
    print(' The End')
except Exception as e:
    print(f'{type(e).__name__}: {str(e)}')

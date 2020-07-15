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

    def trem():
        trem_adder = 1.0 - trem_amount
        return np.sin(x * 6.0) * trem_amount + trem_adder

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
    trem_amount = float(scale_trem.get())
    if key_change_bool[0] is True:
        num_range = c_range
    else:
        num_range = e_range

    x = np.linspace(0, 2 * np.pi * duration,
                    int(duration * sample_rate))
    ramp_0 = np.logspace(1, 0, np.size(x), base=10) * ramp_amount
    attak = np.linspace(0, 1, int(np.size(x) * float(scale_attak.get())))
    fade = np.linspace(1, 0, int(
        np.size(x) * float(scale_fade.get())) + 1)

    notes = []
    for i in num_range:
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

        waveform[:np.size(attak)] *= attak
        waveform[-np.size(fade):] *= fade
        waveform2 = np.roll(waveform, roll_amount, axis=None)
        waveform3 = np.vstack((waveform2, waveform)).T
        if trem_flag.get() is True:
            trem_data = trem().reshape(-1, 1)
            if leftover != 0:
                waveform3 = waveform3 * \
                    np.concatenate((trem_data, extra.reshape(-1, 1)))
            else:
                waveform3 = waveform3 * trem_data
        notes.append(waveform3)

    global key_notes
    key_notes = dict(zip(keys, notes))
    return key_notes


def stream_func():
    def callback(outdata, frames, time, status):
        try:
            data = next(sound_slice)
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


def toggle_trem():
    trem_flag.set(not trem_flag.get())
    if trem_flag.get() is True:
        trem_button.config(bg="#728C00", fg="white", text="Trem On")
    else:
        trem_button.config(bg="#000000", fg="white", text="Tremelo")
    do_it()


def change_key():
    key_change_bool[0] = not key_change_bool[0]
    if key_change_bool[0] is True:
        keys[:] = c_keys[:]
        key_change_button.config(bg="#728C00", fg="white", text='Key of C4')
    else:
        keys[:] = e_keys[:]
        key_change_button.config(bg="#000000", fg="white", text='key of E4')
    for key in unbinders:
        master.unbind(f'<{key}>')
    for key in keys:
        binders(f'{key}')
    do_it()


def binders(la):
    master.bind(f"<{la}>", play_it)


try:
    e_keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
              'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    c_keys = ['a', 'w', 's', 'e', 'd', 'f', 't',
              'g', 'y', 'h', 'u', 'j', 'k', 'o', 'l']

    unbinders = ['w', 'r', 'y', 'i', 'o', 'p']

    keys = []
    keys[:] = e_keys[:]
    c_range = range(-9, 6)
    e_range = range(-5, 10)
    key_change_bool = [False]

    sample_rate = 48000
    blocksize = 256
    fade_amount = 6000
    flag = True
    sound = np.zeros((blocksize, 2))
    sound_slice = gen()
    fade = np.linspace(1, 0, fade_amount)
    stream_thread = threading.Thread(target=stream_func)
    stream_thread.start()

    master = tk.Tk()
    master.geometry('700x500')
    master.configure(padx=20, pady=20)
    master.title("1/4 Dead Emergency")
    trem_flag = tk.BooleanVar()
    trem_flag.set(False)

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
    attak_label = tk.Label(master, text='Attack')
    fade_label = tk.Label(master, text='Fade')
    trem_label = tk.Label(master, text='Tremelo')

    scale_duration = tk.Scale(master, from_=0.1, to=3.0, resolution=0.1,
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
    scale_attak = tk.Scale(master, from_=0.0, to=1.0,
                           resolution=0.02, orient=tk.VERTICAL, length=130)
    scale_fade = tk.Scale(master, from_=0.01, to=1.0,
                          resolution=0.01, orient=tk.VERTICAL, length=130)
    scale_trem = tk.Scale(master, from_=0.0, to=0.5, resolution=0.02,
                          orient=tk.HORIZONTAL, length=200)
    trem_button = tk.Button(master, bg="#000000", fg="white", text='Tremelo',
                            width=7, command=toggle_trem)
    key_change_button = tk.Button(
        master, text='Key of E4', bg="#000000", fg="white", command=change_key)
    close_button = tk.Button(master, text='Close', width=7, command=stop_it)

    scale_duration.set(1.0)
    scale_freq5.set(2.2)
    scale_f1.set(440)
    scale_ramp.set(0.25)
    scale_roll.set(600)
    scale_trem.set(0.46)

    duration_label.grid(row=0, column=0)
    freq5_label.grid(row=1, column=0)
    f1_label.grid(row=2, column=0)
    ramp_label.grid(row=3, column=0)
    roll_label.grid(row=4, column=0)
    sm_label.grid(row=5, column=0)
    tm_label.grid(row=5, column=2, sticky='w')
    trem_label.grid(row=6, column=0)

    scale_duration.grid(row=0, column=1)
    scale_freq5.grid(row=1, column=1)
    scale_f1.grid(row=2, column=1, sticky='w')
    scale_ramp.grid(row=3, column=1)
    scale_roll.grid(row=4, column=1)
    scale_st.grid(row=5, column=1, pady=20)
    scale_trem.grid(row=6, column=1)
    trem_button.grid(row=1, column=2, padx=20)
    key_change_button.grid(row=4, column=2, padx=20)
    close_button.grid(row=6, column=2, padx=20)

    attak_label.grid(row=0, column=3)
    fade_label.grid(row=0, column=4)

    scale_attak.grid(row=1, column=3, rowspan=3)
    scale_fade.grid(row=1, column=4, rowspan=3)

    key_notes = do_it()
    master.protocol("WM_DELETE_WINDOW", on_closing)
    master.mainloop()
except KeyboardInterrupt:
    flag = False
    print(' The End')
except Exception as e:
    flag = False
    print(f'{type(e).__name__}: {str(e)}')

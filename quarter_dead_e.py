#!/usr/bin/env python3

# Copyright (C) 2020 Harry Sentonbury
# GNU General Public License v3.0

import numpy as np
import simpleaudio as sa
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import messagebox


def play_note(event):
    if stop_flag.get() is False:
        sa.stop_all()
    play_obj = sa.play_buffer(key_notes.get(event.char), 2, 2, sample_rate)


def stop_play():
    sa.stop_all()


def on_quitting():
    if messagebox.askokcancel("Quit?", "Shure You Want To Quit"):
        closing()


def closing():
    sa.stop_all()
    master.destroy()


def do_it_int16(place_holder=0):

    def wave_maker(a):
        factor = (2**(a / 12.0))
        waveform_mod = (sine_wave(freq_octave * factor) * sm) + \
            (triangle(freq3 * factor, freq_detune) * tm)
        waveform = (sine_wave(freq_octave * factor) * sm) + \
            (triangle(freq3 * factor) * tm)
        waveform_detune = (sine_wave(freq_octave * factor, freq_detune)
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
    freq_detune = float(scale_detune.get())
    duration = float(scale_duration.get())
    freq_octave = float(scale_octave.get())
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


def binders():
    for key in keys:
        master.bind(f"<{key}>", play_note)


def unbinders():
    for key in keys:
        master.unbind(f"<{key}>")


def reset_default_kb():
    unbinders()
    keys[:] = ['a', 's', 'e', 'd', 'r', 'f', 't',
               'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']
    binders()
    do_it_int16()
    if kb_window is not None:
        kb_window.destroy()


def kb_window_func():

    def x_kb_window():
        if messagebox.askokcancel("Quit ?", "Do you want to quit. Keybindings will be reset to default"):
            reset_default_kb()

    def gen():
        end = 'End'
        start = 0
        while True:
            yield (letter[start], start)
            start += 1
            if start == 15:
                start = 0

    def set_label(event):
        def update_entry():
            entry_label["text"] = " "
            note_label['text'] = wot

            if where == 14:
                binders()

                do_it_int16()
                kb_window.destroy()

            keys[where] = event.char

        not_allowed_label["text"] = " "
        if len(event.keysym) > 1:
            not_allowed_label["text"] = "Key\nNot Allowed"
            return
        wot, where = next(letters)
        entry_label["text"] = event.char
        entry_label.after(500, update_entry)

    unbinders()
    first_note = 'E'
    letter = ['F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B', 'C',
              'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'End', ' ']
    letters = gen()

    global kb_window
    kb_window = tk.Toplevel(master)
    kb_window.grab_set()
    kb_window.geometry("400x200")
    kb_window.title("Custom Keybindings")
    kb_window.configure(padx=20)

    label = tk.Label(kb_window, text="Note:")
    note_label = tk.Label(kb_window, text=first_note, width=4,
                          bg='#21e4e4', font='Times 30')
    bind_to_key_label = tk.Label(kb_window, text="Binding to\n Key:")
    entry_label = tk.Label(
        kb_window, width=4, relief='sunken', font='Times 30')
    not_allowed_label = tk.Label(kb_window, fg='#e41345')
    reset_button = tk.Button(kb_window, text="reset", command=reset_default_kb)
    close_kbw_button = tk.Button(
        kb_window, text="Cancel", command=reset_default_kb)
    kb_window.bind('<Key>', set_label)

    label.grid(row=0, column=0, sticky='e')
    note_label.grid(row=0, column=1, pady=10)
    bind_to_key_label.grid(row=1, column=0, padx=10, sticky='w')
    entry_label.grid(row=1, column=1, padx=20)
    not_allowed_label.grid(row=1, column=2)
    reset_button.grid(row=2, column=3, pady=20)
    close_kbw_button.grid(row=2, column=4, padx=20)

    kb_window.protocol("WM_DELETE_WINDOW", x_kb_window)
    kb_window.attributes('-topmost', 'true')

    kb_window.lift()
    kb_window.focus()


def custom_keyboard():
    if kb_window is None:
        kb_window_func()
        return
    try:
        kb_window.lift()
    except tk.TclError:
        kb_window_func()


try:
    keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
            'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    sample_rate = 48000
    fade_amount = 8000
    fade = np.linspace(1, 0, fade_amount)
    kb_window = None

    master = tk.Tk()
    master.geometry('700x500')
    master.title("1/4 Dead in E4")

    menubar = tk.Menu(master)
    dropdown_menu = tk.Menu(menubar)
    dropdown_menu.add_command(
        label="Set Up Custom Key Binding", command=custom_keyboard)
    dropdown_menu.add_command(
        label="Reset Default qwerty Keybindings", command=reset_default_kb)
    menubar.add_cascade(label="settings", menu=dropdown_menu)
    master.configure(padx=20, pady=20, menu=menubar)

    stop_flag = tk.BooleanVar()
    stop_flag.set(False)

    binders()
    master.bind("<ButtonRelease-1>", do_it_int16)

    duration_label = tk.Label(master, text='Duration')
    detune_label = tk.Label(master, text='Detune')
    octave_label = tk.Label(master, text='Sine Octave')
    ramp_label = tk.Label(master, text='Ramp')
    roll_label = tk.Label(master, text='Delay')
    sm_label = tk.Label(master, text='Sine')
    tm_label = tk.Label(master, text='Triangle')

    scale_duration = tk.Scale(master, from_=0.2, to=5.0, resolution=0.2,
                              orient=tk.HORIZONTAL, length=200)
    scale_detune = tk.Scale(master, from_=0.0, to=13.0,
                            resolution=0.2, orient=tk.HORIZONTAL, length=200)
    scale_octave = tk.Scale(master, from_=220, to=440,
                            resolution=220, orient=tk.HORIZONTAL, length=50)
    scale_ramp = tk.Scale(master, from_=0.0, to=2.0,
                          resolution=0.01, orient=tk.HORIZONTAL, length=200)
    scale_roll = tk.Scale(master, from_=0, to=4000,
                          resolution=50, orient=tk.HORIZONTAL, length=200)
    scale_st = tk.Scale(master, from_=0.0, to=1.0,
                        resolution=0.005, orient=tk.HORIZONTAL, length=200, showvalue=0)

    stop_it_button = tk.Button(
        master, text='Stop', width=7, command=stop_play)
    toggle_button = tk.Button(master, text='Mono',
                              bg="#000000", fg="white", width=7, command=toggle_flag)
    close_button = tk.Button(master, text='Close', width=7, command=closing)
    scale_duration.set(1.0)
    scale_detune.set(2.2)
    scale_octave.set(440)
    scale_ramp.set(0.25)
    scale_roll.set(600)

    duration_label.grid(row=0, column=0)
    detune_label.grid(row=1, column=0)
    octave_label.grid(row=2, column=0)
    ramp_label.grid(row=3, column=0)
    roll_label.grid(row=4, column=0)
    sm_label.grid(row=5, column=0)
    tm_label.grid(row=5, column=2, sticky='w')

    scale_duration.grid(row=0, column=1)
    scale_detune.grid(row=1, column=1)
    scale_octave.grid(row=2, column=1, sticky='w')
    scale_ramp.grid(row=3, column=1)
    scale_roll.grid(row=4, column=1)
    scale_st.grid(row=5, column=1, pady=20)
    stop_it_button.grid(row=0, column=2, padx=20)
    toggle_button.grid(row=2, column=2, padx=20)
    close_button.grid(row=6, column=2, padx=20)

    key_notes = do_it_int16()

    master.protocol("WM_DELETE_WINDOW", on_quitting)
    master.mainloop()
except KeyboardInterrupt:
    print(' The End')
except Exception as e:
    print(f'{type(e).__name__}: {str(e)}')

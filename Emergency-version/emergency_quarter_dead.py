#!/usr/bin/env python3

import numpy as np
import sounddevice as sd
import threading
import time
import os
import tkinter as tk
from tkinter import messagebox


def on_closing():
    if messagebox.askokcancel("Quit?", "Do You Want To Quit"):
        stop_it()


def play_it(event):
    global sound
    sound = key_notes.get(event.char)


def stop_it():
    master.destroy()
    flags[0] = False


def do_it(place_holder=0):
    """creates a dictionary of key : notes"""
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
    freq_detune = float(scale_detune.get())
    duration = float(scale_duration.get())
    freq_octave = float(scale_octave.get())
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
    fade_size = int(np.size(x) * float(scale_fade.get()))
    attak = np.linspace(0, 1, int(np.size(x) * float(scale_attak.get())))
    fade = np.linspace(1, 0, fade_size if fade_size >= 1 else 1)

    notes = []
    for i in num_range:
        factor = (2**(i / 12.0))
        waveform_mod = (sine_wave(freq_octave * factor) * sm) + \
            (triangle(freq3 * factor, freq_detune) * tm)
        waveform = (sine_wave(freq_octave * factor) * sm) + \
            (triangle(freq3 * factor) * tm)
        waveform_detune = (sine_wave(freq_octave * factor, freq_detune)
                           * sm) + (triangle(freq3 * factor) * tm)

        waveform = ((waveform + waveform_detune) *
                    (waveform_mod / 2 + 0.5)) * 0.1

        leftover = np.size(waveform) // blocksize != 0
        if leftover != 0:
            extra = np.zeros(blocksize - leftover)
            waveform = np.concatenate((waveform, extra))

        waveform[:np.size(attak)] *= attak
        waveform[-np.size(fade):] *= fade
        waveform2 = np.roll(waveform, roll_amount)
        waveform3 = np.vstack((waveform2, waveform)).T
        if flags[1] is True:
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


def stream_func(device=-1):
    def callback(outdata, frames, time, status):
        try:
            data = next(sound_slice)
            if flags[0] == False:
                raise sd.CallbackStop
            else:
                outdata[:, :] = data
        except ValueError:
            outdata[:, :] = np.zeros((blocksize, 2))

    device = device if device >= 0 else None
    stream = sd.OutputStream(device=device, channels=2, callback=callback, blocksize=blocksize,
                             samplerate=sample_rate)
    with stream:
        while flags[0] == True:
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
    flags[1] = not flags[1]
    if flags[1] is True:
        trem_button.config(bg="#728C00", fg="white", text="Trem On")
    else:
        trem_button.config(bg="#000000", fg="white", text="tremolo")
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


def message_win_func(mtitle, blah):

    def closer():
        ms_win.destroy()

    global ms_win
    ms_win = tk.Toplevel(master)
    ms_win.title(mtitle)
    label = tk.Label(ms_win, text=blah, font='Times 20')
    button = tk.Button(ms_win, text='OK', width=6,
                       bg="#728C00", fg="white", command=closer)
    ms_win.bind('<Return>', lambda event=None: button.invoke())

    label.pack(padx=30, pady=10)
    button.pack(pady=20)
    ms_win.lift()


def message_win(mtitle, blah):
    if ms_win is None:
        message_win_func(mtitle, blah)
        return
    try:
        ms_win.lift()
    except tk.TclError:
        message_win_func(mtitle, blah)


def diagram_func():
    """shows images of key bindings"""
    def closer():
        diagram_window.destroy()

    try:
        global diagram_window
        diagram_window = tk.Toplevel(master)
        diagram_window.title('Diagram')
        label_c = tk.Label(diagram_window, image=image_c)
        label_e = tk.Label(diagram_window, image=image_e)
        close_button = tk.Button(diagram_window, text='Close', command=closer)

        label_c.grid(row=0, column=0, padx=20, pady=10)
        label_e.grid(row=1, column=0, padx=20, pady=10)
        close_button.grid(row=2, column=0)
        diagram_window.lift()
    except NameError as e:
        diagram_window.destroy()
        message_win(type(e).__name__, "No Diagrams Available")


def diagram():
    if diagram_window is None:
        diagram_func()
        return
    try:
        diagram_window.lift()
    except tk.TclError:
        diagram_func()


def device_window_func():
    """Output device dialog"""

    def driver_setter():
        if ms_win is not None:
            ms_win.destroy()
        num = list_bx.curselection()[0]
        num_name = sd.query_devices()[num].get('name')
        try:
            check_driver = sd.check_output_settings(
                device=num, channels=2, dtype='float32', samplerate=sample_rate)
            device_num.set(num)
            stream_restart()
            message_win(
                'Driver Set', '''Device number {} ({}) \n set as output device
                '''.format(num, num_name))
        except sd.PortAudioError:
            message_win('sd.PortAudioError',
                        'Device number {} ({}) \n is not supported. Try another'.format(num, num_name))

    def reset_default():
        device_num.set(-1)
        stream_restart()
        if ms_win is not None:
            ms_win.destroy()
        message_win("Default Device", "Device set to default")

    def stream_restart():
        flags[0] = True
        stream_thread = threading.Thread(
            target=stream_func, args=[device_num.get()])
        stream_thread.start()
        device_window.destroy()

    def on_closing_dw():
        if messagebox.askokcancel('Question', 'Do you want to restart stream?'):
            stream_restart()

    flags[0] = False
    global device_window
    device_window = tk.Toplevel(master)
    device_window.title('Output Devices')
    device_window.config(bg='#afb4b5')

    query = repr(sd.query_devices())
    query = query.split('\n')

    frame_0 = tk.Frame(device_window, relief=tk.RAISED, bd=2, bg='#afb4b5')
    label_0 = tk.Label(device_window, text='List of availible devices',
                       bg='#afb4b5', font='Times 20')
    scrollbar = tk.Scrollbar(device_window)
    label_1 = tk.Label(
        frame_0, text='Select output device then set', bg='#afb4b5', font='Times 15')
    set_device_button = tk.Button(frame_0, text='Set', height=3, width=6, activebackground='#99c728',
                                  bg="#728C00", fg="white", command=driver_setter)
    reset_button = tk.Button(
        device_window, text='Reset to Default Device', command=reset_default)
    cancel_button = tk.Button(
        device_window, text='Cancel', command=stream_restart)
    list_bx = tk.Listbox(
        device_window, yscrollcommand=scrollbar.set, width=60, height=25)
    for i in range(len(query)):
        list_bx.insert(tk.END, query[i])

    label_0.grid(row=0, column=0, columnspan=2)
    list_bx.grid(row=1, column=0, columnspan=3)
    scrollbar.grid(row=1, column=3, sticky=tk.N + tk.S)
    label_1.grid(row=2, column=0, sticky='ne', pady=8, padx=5)
    frame_0.grid(row=2, column=0, rowspan=2, columnspan=2,
                 sticky='w', pady=5, padx=20)
    set_device_button.grid(row=3, column=1, pady=5, padx=5)
    cancel_button.grid(row=3, column=2, sticky='w')
    reset_button.grid(row=4, column=1, sticky='w', pady=8)
    scrollbar.config(command=list_bx.yview)

    device_window.protocol('WM_DELETE_WINDOW', on_closing_dw)
    device_window.lift()


def device_select():
    if device_window is None:
        device_window_func()
        return
    try:
        device_window.lift()
    except tk.TclError:
        device_window_func()


try:
    e_keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
              'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    c_keys = ['a', 'w', 's', 'e', 'd', 'f', 't',
              'g', 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p']

    unbinders = ['w', 'r', 'y', 'i', 'o']

    keys = []
    keys[:] = e_keys[:]
    c_range = range(-9, 7)
    e_range = range(-5, 10)
    key_change_bool = [False]

    sample_rate = 48000
    blocksize = 256
    fade_amount = 6000
    flags = [True, False]   # [stream flag, tremolo flag]
    diagram_window = None
    device_window = None
    ms_win = None
    sound = np.zeros((blocksize, 2))
    sound_slice = gen()
    fade = np.linspace(1, 0, fade_amount)
    stream_thread = threading.Thread(target=stream_func)
    stream_thread.start()

    master = tk.Tk()
    master.geometry('700x500')
    master.configure(padx=20, pady=20)
    master.title("1/4 Dead Emergency")
    device_num = tk.IntVar()
    device_num.set(-1)

    for key in keys:
        binders(f'{key}')
    master.bind("<ButtonRelease-1>", do_it)

    menu_bar = tk.Menu(master)
    menu_bar.add_command(label='Keyboard Diagram', command=diagram)
    menu_bar.add_command(label='Output', command=device_select)
    master.config(menu=menu_bar)

    try:        # Runnig in Atom throws an error! (Script package)
        image_c = tk.PhotoImage(file='media/kb_c.gif')
        image_e = tk.PhotoImage(file='media/kb_e.gif')
    except tk.TclError:     # But this works?
        if os.path.exists('images/kb_c.gif') and os.path.exists('images/kb_e.gif'):
            image_c = tk.PhotoImage(file='images/kb_c.gif')
            image_e = tk.PhotoImage(file='images/kb_e.gif')
        else:
            print('no keyboard layout diagrams but who cares')

    duration_label = tk.Label(master, text='Duration')
    detune_label = tk.Label(master, text='Detune')
    octave_label = tk.Label(master, text='Sine Octave')
    ramp_label = tk.Label(master, text='Ramp')
    roll_label = tk.Label(master, text='Delay')
    sm_label = tk.Label(master, text='Sine')
    tm_label = tk.Label(master, text='Triangle')
    attak_label = tk.Label(master, text='Attack')
    fade_label = tk.Label(master, text='Fade')
    trem_label = tk.Label(master, text='Tremolo')

    scale_duration = tk.Scale(master, from_=0.1, to=3.0, resolution=0.1,
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
    scale_attak = tk.Scale(master, from_=0.0, to=1.0,
                           resolution=0.02, orient=tk.VERTICAL, length=130)
    scale_fade = tk.Scale(master, from_=0.01, to=1.0,
                          resolution=0.01, orient=tk.VERTICAL, length=130)
    scale_trem = tk.Scale(master, from_=0.0, to=0.5, resolution=0.02,
                          orient=tk.HORIZONTAL, length=200)
    key_change_button = tk.Button(
        master, text='Key of E4', bg="#000000", fg="white", command=change_key)
    trem_button = tk.Button(master, bg="#000000", fg="white", text='tremolo',
                            width=7, command=toggle_trem)
    close_button = tk.Button(master, text='Close', width=7, command=stop_it)

    scale_duration.set(1.0)
    scale_detune.set(2.2)
    scale_octave.set(440)
    scale_ramp.set(0.25)
    scale_roll.set(600)
    scale_trem.set(0.46)

    duration_label.grid(row=0, column=0)
    detune_label.grid(row=1, column=0)
    octave_label.grid(row=2, column=0)
    ramp_label.grid(row=3, column=0)
    roll_label.grid(row=4, column=0)
    sm_label.grid(row=5, column=0)
    tm_label.grid(row=5, column=2, sticky='w')
    trem_label.grid(row=6, column=0)

    scale_duration.grid(row=0, column=1)
    scale_detune.grid(row=1, column=1)
    scale_octave.grid(row=2, column=1, sticky='w')
    scale_ramp.grid(row=3, column=1)
    scale_roll.grid(row=4, column=1)
    scale_st.grid(row=5, column=1, pady=20)
    scale_trem.grid(row=6, column=1)
    trem_button.grid(row=6, column=2, padx=20)
    key_change_button.grid(row=2, column=2, padx=20)
    close_button.grid(row=7, column=2, padx=20, pady=20)

    attak_label.grid(row=0, column=3)
    fade_label.grid(row=0, column=4)

    scale_attak.grid(row=1, column=3, rowspan=3)
    scale_fade.grid(row=1, column=4, rowspan=3)

    key_notes = do_it()
    master.protocol("WM_DELETE_WINDOW", on_closing)
    master.mainloop()
except KeyboardInterrupt:
    flags[0] = False
    print(' The End')
except Exception as e:
    flags[0] = False
    print(f'{type(e).__name__}: {str(e)}')

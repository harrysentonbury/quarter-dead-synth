#!/usr/bin/env python3

# Copyright (C) 2020 Harry Sentonbury
# GNU General Public License v3.0

import os
import threading
import time

import mido
import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import messagebox
import Pmw


def on_closing():
    if messagebox.askokcancel("Quit?", "Do You Want To Quit"):
        stop_it()


def play_it(event):
    global sound
    sound = key_notes.get(event.char)


def stop_it():
    master.destroy()
    flags_stream_trem[0] = False


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

    applying_sliders_flag[0] = True
    update_sliders_button.config(text="Wait", state="disabled")
    update_sliders_button.update()
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
    if midi_on_flag[0] is True:
        num_range = midi_range
        keys[:] = note_nums[:]
    else:
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

        waveform[:np.size(attak)] *= attak
        waveform[-np.size(fade):] *= fade
        waveform2 = np.roll(waveform, roll_amount)
        waveform3 = np.vstack((waveform2, waveform)).T
        if flags_stream_trem[1] is True:
            trem_data = trem().reshape(-1, 1)
            waveform3 = waveform3 * trem_data
        notes.append(waveform3)

    global key_notes
    key_notes = dict(zip(keys, notes))
    applying_sliders_flag[0] = False
    update_sliders_button.update()
    update_sliders_button.config(text="Apply Slider Changes", state="normal")
    return key_notes


def stream_func(device=-1, chunk=256):
    def callback(outdata, frames, time, status):
        try:
            data = next(sound_slice)
            if flags_stream_trem[0] == False:
                raise sd.CallbackStop
            else:
                outdata[:, :] = data
        except ValueError:
            outdata[:, :] = np.zeros((blocksize, 2))

    def gen():
        global sound
        sound = np.zeros((blocksize, 2))
        while True:
            slice = sound[:blocksize, :]
            yield slice
            sound = sound[blocksize:, :]

    blocksize = chunk
    sound_slice = gen()
    device = device if device >= 0 else None
    stream = sd.OutputStream(device=device, channels=2, callback=callback, blocksize=blocksize,
                             samplerate=sample_rate)
    with stream:
        while flags_stream_trem[0] == True:
            time.sleep(0.5)
        else:
            stream.__exit__()


def toggle_trem():
    flags_stream_trem[1] = not flags_stream_trem[1]
    if flags_stream_trem[1] is True:
        trem_button.config(bg="#728C00", fg="white", text="Trem On")
    else:
        trem_button.config(bg="#000000", fg="white", text="tremolo")
    if midi_on_flag[0] is True:
        return
    else:
        do_it()


def change_key():
    if midi_on_flag[0] is True:
        return
    else:
        unbinders()
        key_change_bool[0] = not key_change_bool[0]
        if key_change_bool[0] is True:
            keys[:] = c_keys[:]
            key_change_button.config(
                bg="#728C00", fg="white", text='Key of C4')
        else:
            keys[:] = e_keys[:]
            key_change_button.config(
                bg="#000000", fg="white", text='key of E4')
        binders()
        do_it()


def unbinders():
    for key in keys:
        master.unbind(f'<{key}>')


def binders():
    for key in keys:
        master.bind(f"<{key}>", play_it)


def message_win_func(mtitle, blah):
    global ms_win
    ms_win = tk.Toplevel(master)
    ms_win.title(mtitle)
    if is_icon[0] is True:
        ms_win.iconphoto(False, icon_image)
    label = tk.Label(ms_win, text=blah, font='Times 20')
    button = tk.Button(ms_win, text='OK', width=6,
                       bg="#728C00", fg="white", command=lambda: ms_win.destroy())
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
        if is_icon[0] is True:
            diagram_window.iconphoto(False, icon_image)
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
        if list_bx.curselection() == ():
            message_win(
                'Oi!', '''Select a device \n from the list or cancel
                ''')
            return
        num = list_bx.curselection()[0]
        num_name = sd.query_devices()[num].get('name')
        try:
            check_driver = sd.check_output_settings(
                device=num, channels=2, dtype='float32', samplerate=sample_rate)
            device_num.set(num)
            stream_restart(new_blocksize[0])
            message_win(
                'Driver Set', '''Device number {} ({}) \n set as output device.\n Blocksize = {}
                '''.format(num, num_name, new_blocksize))
        except sd.PortAudioError:
            message_win('sd.PortAudioError',
                        'Device number {} ({}) \n is not supported. Try another'.format(num, num_name))

    def reset_default():
        device_num.set(-1)
        new_blocksize[0] = default_blocksize
        stream_restart()
        if ms_win is not None:
            ms_win.destroy()
        message_win("Default Device", f"Device set to default.\nBlocksize = {default_blocksize}")

    def stream_restart(chunk_size=256):
        flags_stream_trem[0] = True
        stream_thread = threading.Thread(
            target=stream_func, args=[device_num.get(), chunk_size])
        stream_thread.start()
        device_window.destroy()

    def show_blocksize(event):
        new_blocksize_val = 2**int(event)
        blocksize_label['text'] = f"Blocksize = {str(new_blocksize_val)}"
        new_blocksize[0] = new_blocksize_val

    def on_closing_dw():
        if messagebox.askokcancel('Question', 'Do you want to close Output Devices window?'):
            new_blocksize[0] = default_blocksize
            stream_restart()

    flags_stream_trem[0] = False
    global device_window
    device_window = tk.Toplevel(master)
    device_window.title('Output Devices And Blocksize')
    device_window.config(bg='#afb4b5')
    if is_icon[0] is True:
        device_window.iconphoto(False, icon_image)

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
        device_window, text='Reset to Defaults', command=reset_default)
    scale_blocksize = tk.Scale(device_window, label="Set Blocksize", from_=8,
                               to=11, orient=tk.HORIZONTAL, showvalue=False, command=show_blocksize)
    scale_blocksize.set(int(np.log2(new_blocksize)))
    blocksize_label = tk.Label(device_window, text=f'Blocksize = {str(new_blocksize[0])}', width=14)
    cancel_button = tk.Button(
        device_window, text='Close', command=lambda: stream_restart(new_blocksize[0]))
    list_bx = tk.Listbox(
        device_window, yscrollcommand=scrollbar.set, width=60, height=25)
    for i in range(len(query)):
        list_bx.insert(tk.END, query[i])
    list_bx.selection_set(tk.END)

    label_0.grid(row=0, column=0, columnspan=2)
    list_bx.grid(row=1, column=0, columnspan=3)
    scrollbar.grid(row=1, column=3, sticky=tk.N + tk.S)
    label_1.grid(row=2, column=0, sticky='ne', pady=8, padx=5)
    frame_0.grid(row=2, column=0, rowspan=2, columnspan=2,
                 sticky='w', pady=5, padx=20)
    scale_blocksize.grid(row=2, column=2)
    blocksize_label.grid(row=3, column=2, sticky='n')
    set_device_button.grid(row=3, column=1, pady=5, padx=5)
    cancel_button.grid(row=4, column=2, sticky='w')
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


def reset_default_kb(is_c):
    if midi_on_flag[0] is True:
        return
    else:
        unbinders()
        if is_c is False:
            e_keys[:] = ['a', 's', 'e', 'd', 'r', 'f', 't',
                         'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']
            keys[:] = e_keys[:]
        else:
            c_keys[:] = ['a', 'w', 's', 'e', 'd', 'f', 't',
                         'g', 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p']
            keys[:] = c_keys[:]
        binders()
        do_it()
        if kb_window is not None:
            kb_window.destroy()


def kb_window_func(is_c):

    def x_kb_window():
        if messagebox.askokcancel("Quit ?", "Do you want to quit. Keybindings will be reset to default"):
            reset_default_kb(is_c)

    def gen(number_of_notes=15):
        end = 'End'
        start = 0
        while True:
            if number_of_notes == 15:
                yield (letter[start], start)
            else:
                yield (c_letter[start], start)
            start += 1
            if start == number_of_notes:
                start = 0

    def set_label(event):
        def update_entry():
            entry_label["text"] = " "
            if is_c is False:
                wot, where = next(e_letters)
                note_label['text'] = wot

                if where == 14:
                    keys[:] = e_keys[:]
                    binders()
                    do_it()
                    kb_window.destroy()
                e_keys[where] = event.char
            else:
                wot, where = next(c_letters)
                note_label['text'] = wot

                if where == 15:
                    keys[:] = c_keys[:]
                    binders()
                    do_it()
                    kb_window.destroy()
                c_keys[where] = event.char

        not_allowed_label["text"] = " "
        if len(event.keysym) > 1:
            not_allowed_label["text"] = "Key\nNot Allowed"
            return
        entry_label["text"] = event.char
        entry_label.after(500, update_entry)

    unbinders()

    if is_c is False:
        first_note = 'E'
    else:
        first_note = 'C'
    letter = ['F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B', 'C',
              'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'End', ' ']
    c_letter = ['Db', 'D', 'Eb', 'E', 'F', 'Gb',
                'G', 'Ab', 'A', 'Bb', 'B', 'Cb', 'C', 'Db', 'D', 'End', ' ']
    e_letters = gen(number_of_notes=15)
    c_letters = gen(number_of_notes=16)

    global kb_window
    kb_window = tk.Toplevel(master)
    kb_window.grab_set()
    kb_window.geometry("500x200")
    if is_c is False:
        kb_window.title("Custom Keybindings for E4")
    else:
        kb_window.title("Custom Keybindings for C4")
    kb_window.configure(padx=20)
    if is_icon[0] is True:
        kb_window.iconphoto(False, icon_image)

    label = tk.Label(kb_window, text="Note:")
    note_label = tk.Label(kb_window, text=first_note, width=4,
                          bg='#0ba4a4', font='Times 30')
    bind_to_key_label = tk.Label(kb_window, text="Binding\nTo Key")
    entry_label = tk.Label(
        kb_window, width=4, relief='sunken', font='Times 30')
    not_allowed_label = tk.Label(kb_window, fg='#e41345')
    reset_button = tk.Button(kb_window, text="Reset Default",
                             command=lambda: reset_default_kb(is_c))
    close_kbw_button = tk.Button(
        kb_window, text="Cancel", command=lambda: reset_default_kb(is_c))
    kb_window.bind('<Key>', set_label)
    tool_tip = Pmw.Balloon(kb_window)
    tool_tip.bind(
        entry_label, "Type the keys that you want binding\nto the above notes displayed in blue")

    label.grid(row=0, column=0, sticky='e')
    note_label.grid(row=0, column=1, pady=10)
    bind_to_key_label.grid(row=1, column=0, padx=10, sticky='w')
    entry_label.grid(row=1, column=1, padx=20)
    not_allowed_label.grid(row=1, column=2)
    reset_button.grid(row=2, column=3, pady=20)
    close_kbw_button.grid(row=2, column=4, padx=20)

    kb_window.protocol("WM_DELETE_WINDOW", x_kb_window)
    kb_window.lift()
    kb_window.focus()


def custom_keyboard(is_c):
    if midi_on_flag[0] is True:
        return
    else:
        if kb_window is None:
            kb_window_func(is_c)
            return
        try:
            kb_window.lift()
        except tk.TclError:
            kb_window_func(is_c)


def choose_port_func():
    def select_input():
        master.unbind("<ButtonRelease-1>")
        unbinders()
        midi_on_flag[0] = True
        if list_box.curselection() == ():
            print("Nope")
            return
        # port_name[0] = list_box.get(list_box.curselection())
        # print(port_name[0])
        do_it()
        activate_midi(list_box.get(list_box.curselection()))
        port_window.destroy()

    midi_input_names = mido.get_input_names()
    global port_window
    port_window = tk.Toplevel(master)

    label_0 = tk.Label(port_window, text="Input Names")
    scrollbar = tk.Scrollbar(port_window)
    list_box = tk.Listbox(
        port_window, yscrollcommand=scrollbar.set, width=60, height=15)
    for i in midi_input_names:
        list_box.insert(tk.END, i)
    list_box.selection_set(tk.END)
    select_button = tk.Button(port_window, text="Select", bg="#728C00",
                              fg="white", command=select_input)
    close_midi_win_button = tk.Button(port_window, text="Close",
                                      command=lambda: port_window.destroy())

    label_0.grid(row=0, column=0)
    list_box.grid(row=1, column=0, columnspan=2)
    scrollbar.grid(row=1, column=2, sticky=tk.N + tk.S)
    scrollbar.config(command=list_box.yview)
    select_button.grid(row=2, column=0, pady=10)
    close_midi_win_button.grid(row=2, column=1)
    port_window.lift()


def choose_port():
    if port_window is None:
        choose_port_func()
    try:
        port_window.lift()
    except tk.TclError:
        choose_port_func()


def midi_stuff(port_arg):
    def play_note(event):
        global key_notes
        if applying_sliders_flag[0] is True:
            return
        else:
            try:
                global sound
                sound = key_notes.get(event)
                # print(key_notes.get(event).type)
            except TypeError:
                return

    if len(port_arg) > 1:
        portname = port_arg
    else:
        portname = None  # Use default port

    with mido.open_input(portname) as port:
        print('Using {}'.format(port))
        print('Waiting for messages...')
        for message in port:
            if message.type == 'note_on' and message.velocity > 0:
                play_note(message.note)


def activate_midi(port_arg):
    midi_thread = threading.Thread(
        target=midi_stuff, args=[port_arg], daemon=True)
    midi_thread.start()


try:
    e_keys = ['a', 's', 'e', 'd', 'r', 'f', 't',
              'g', 'h', 'u', 'j', 'i', 'k', 'l', 'p']

    c_keys = ['a', 'w', 's', 'e', 'd', 'f', 't',
              'g', 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p']

    note_nums = [i for i in range(36, 97)]
    midi_on_flag = [False]
    port_name = [None]
    applying_sliders_flag = [True]
    keys = []
    keys[:] = e_keys[:]
    c_range = range(-9, 7)
    e_range = range(-5, 10)
    midi_range = range(-33, 28)
    key_change_bool = [False]

    sample_rate = 48000
    default_blocksize = 256
    new_blocksize = [default_blocksize]
    fade_amount = 6000
    flags_stream_trem = [True, False]   # [stream flag, tremolo flag]
    diagram_window = None
    device_window = None
    ms_win = None
    kb_window = None
    port_window = None
    fade = np.linspace(1, 0, fade_amount)
    stream_thread = threading.Thread(
        target=stream_func, args=[-1, default_blocksize])
    stream_thread.start()

    master = tk.Tk()
    Pmw.initialise(master)
    master.geometry('700x500')
    master.configure(padx=20, pady=20)
    master.title("1/4 Dead Emergency")
    device_num = tk.IntVar()
    device_num.set(-1)
    is_icon = ['False']

    binders()
    master.bind("<ButtonRelease-1>", do_it)

    # Runnig in Atom will not find media dir! (Script package)
    if os.path.exists('./media/kb_c.gif') and os.path.exists(
            './media/kb_e.gif')and os.path.exists('./media/knotperfect-icon.gif'):
        image_c = tk.PhotoImage(file='./media/kb_c.gif')
        image_e = tk.PhotoImage(file='./media/kb_e.gif')
        icon_image = tk.PhotoImage(file="./media/knotperfect-icon.gif")
        master.iconphoto(False, icon_image)
        is_icon[0] = True
    else:
        print('no keyboard layout diagrams but who cares')

    menu_bar = tk.Menu(master)
    dropdown_settings = tk.Menu(menu_bar)
    dropdown_settings.add_command(label='Keyboard Diagram', command=diagram)
    dropdown_settings.add_command(
        label='Select Output Device And Blocksize', command=device_select)
    dropdown_settings.add_command(
        label="Set Up Custom Key Binding", command=lambda: custom_keyboard(key_change_bool[0]))
    dropdown_settings.add_command(
        label="Reset Default qwerty Keybindings", command=lambda: reset_default_kb(key_change_bool[0]))
    dropdown_settings.add_command(label='Open Midi Port', command=choose_port)
    menu_bar.add_cascade(label="settings", menu=dropdown_settings)
    master.config(menu=menu_bar)

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
    update_sliders_button = tk.Button(master, text="Apply Slider Changes",
                                      bg="#728C00", fg="white", width=18, command=do_it)
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
    update_sliders_button.grid(row=7, column=1, sticky='W')
    close_button.grid(row=7, column=2, padx=20, pady=20)

    attak_label.grid(row=0, column=3)
    fade_label.grid(row=0, column=4)

    scale_attak.grid(row=1, column=3, rowspan=3)
    scale_fade.grid(row=1, column=4, rowspan=3)

    key_notes = do_it()
    master.protocol("WM_DELETE_WINDOW", on_closing)
    master.mainloop()
except KeyboardInterrupt:
    flags_stream_trem[0] = False
    print(' The End')
except Exception as e:
    flags_stream_trem[0] = False
    print(f'{type(e).__name__}: {str(e)}')

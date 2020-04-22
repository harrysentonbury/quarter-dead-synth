# quarter-dead-synth

### A bit of a synthesizer you can play on your computer keyboard.

I called it quarter dead because that was the first tune that popped out
of my fingers after I tapped a key and heard the first note. It uses
simpleaudio, its a fantastic package, I just discovered it. I am pretty
sure you need at least python 3.7 to use it. Also numpy, and tkinter for the GUI.
The quarter-dead-synth has detune functionality, Switch between two octaves.
Adjustable FM modifying ramp intensity. There is a delay slider to
delay the left channel but, -there is a surprise!

There is the original version in the key of C4.

![qdc-layout](images/kb_c.jpg)

Or the "quarter_dead_e" in E4 with
added functionality. You can swing between sine and triangle waves.
Switch just the sine between two octaves.
And, switch between monophonic and polyphonic.

![qde-layout](images/kb_e.jpg)

## python3.7 +

### Linux prerequisites for simpleaudio

```
sudo pip3 install --upgrade pip setuptools
```
```
sudo apt-get install -y python3-dev libasound2-dev
```

### dependences

```
pip3 install numpy
pip3 install simpleaudio
```
Also tkinter.

```
sudo apt-get install python-tk
```

![qdgui-layout](images/qds_gui.jpg)

# Emergency-version

**Disadvantages**
  - It is monophonic only.
  - Does not sound as good.

**Advantages**
  - It can be recorded with audacity and the like.
  - Probably works on all computers.
  - Its got tremolo.
  - Its got attack and fade.
  - Switch between C4 and E4.
  - Plug in a midi

This one uses sounddevice OutputStream instead of simpleaudio.
The images below shows the keyboard layout
for C4 and E4 respectively.

Set Output Device and Blocksize from the dialog accessed from the drop down menu.
Maybe for a usb audio interface for example. The blocksize of can be adjusted with the slider.
You can make a selection from the devices list and click 'Set'.

Open a midi port from dialogue accessed from the dropdown menu. Select an input name
then click 'Select'. Wait a few seconds then your good to go.

![qde-layout](../images/kb_c.jpg)

![qde-layout](../images/kb_e.jpg)

### dependences

```
pip3 install numpy
pip3 install sounddevice
```
Also tkinter.

```
sudo apt-get install python-tk
```

![eqds-layout](../images/eqds_tr0.jpg)

Listen to these synths on this crap video : [https://youtu.be/WFZZJfIEdT4](https://youtu.be/WFZZJfIEdT4).

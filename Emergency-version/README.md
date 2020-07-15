# Emergency-version

**Disadvantages**
  - It is monophonic only.
  - Does not sound as good.

**Advantages**
  - It can be recorded with audacity and the like.
  - Probably works on all computers.
  - Its got tremelo.
  - Its got attack and fade.
  - Switch between C4 and E4.

This one uses sounddevice instead of simpleaudio.
It uses a callback function that streams zeros if no key
has been pressed. The images below shows the keyboard layout
for C4 and E4 respectively.

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

Listen to these synths on this video : [https://youtu.be/WFZZJfIEdT4](https://youtu.be/WFZZJfIEdT4).

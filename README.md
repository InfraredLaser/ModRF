## Modulating Retro Reflector

This repository contains a sqequence of scripts to perform comms with 
Liquid Crystals in a modulated retro reflector setup.

### How scripts works
    - recv.py has two functions
        1) Sends modulating voltage signals to a DAQ Analog Output buffer
        2) Reads detector signal from ADC buffer and process buffer that translates binary string to individual characters.
    - recv.py runs a subprocess (send.py) which builds the modulating waveform in the AO buffer

## How to run scripts
Run recv.py in terminal to see comm output.

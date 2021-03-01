"""this skript runs the Attemplifier through its values"""

from .attenuatorMain import select_att
from .attenuatorMain import attenuate
from .attenuatorMain import latchEnable
import time

def main():


    select_att(1)
    attenuate(0)
    latchEnable()
    print('Setup Attemplifier with 0dB attenuation')

    time.sleep(5)
    input("Press Enter to continue...")
    for x in range(6):
        steps = [0.5, 1, 2, 4, 8, 16]
        select_att(1)
        attenuate(steps[x])
        latchEnable()
        print('Set Attenuation to: '+steps+'dB')
        time.sleep(5)









if __name__== "__main__":

    main()
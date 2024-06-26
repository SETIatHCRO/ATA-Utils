"""this skript runs the Attemplifier through its values"""

from attenuatorMain.attenuatorMain import select_att
from attenuatorMain.attenuatorMain import attenuate
from attenuatorMain.attenuatorMain import latchEnable
import time

def main():


    select_att(1)
    attenuate(0)
    latchEnable()
    print('Setup Attemplifier with 0dB attenuation')
    input("Press Enter to continue...")
    for x in range(6):
        steps = [0.5, 1, 2, 4, 8, 16]
        select_att(1)
        attenuate(steps[x])
        latchEnable()
        print('Set Attenuation to: '+str(steps[x])+'dB')
        time.sleep(3)









if __name__== "__main__":

    main()

from labjack import ljm
from framework import Sensor

class PDA36A(Sensor):
    """
    A Sensor to measure the output of a PDA36A sensor with a Labjack
    """

    _labjack = None

    def __init__(self):
        self._labjack = ljm.openS("ANY", "ANY", "ANY")

        print("Serial number:", ljm.eReadName(self._labjack, 'SERIAL_NUMBER'))

import pyforms
from pyforms import BaseWidget
from pyforms.Controls import ControlList

class ControllerWindow(BaseWidget):

    def __init__(self):
        BaseWidget.__init__(self)
        self._controlAxisList = ControlList("Control Axis", add_function = self.__addControlAxis, remove_function = self.__removeControlAxis)
        self._controlAxisList.horizontalHeaders = ['Name']

    def add_control_axis(self, control_axis):
        self._controlAxisList += [control_axis]

    def remove_control_axis(self, index):
        self._controlAxisList -= index

    def __addControlAxis(self):
        self.add_control_axis("Hello")

    def __removeControlAxis(self):
        self.remove_control_axis(0)
    
pyforms.start_app(ControllerWindow)
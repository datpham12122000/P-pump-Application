from PySide6.QtCore import (Qt, QDateTime, Slot,
                            QTimer, Signal,QObject)
from graph import *

class GraphManager(QObject):
    updatePressureDataBasedOnIDSignal = Signal(int,QDateTime,float,float,float)
    def __init__(self , parent = None):
        super().__init__(parent)
    
    def initializeInternalVar(self,available_node : list[int] , pressure_unit: str, min_pressure: float , max_pressure: float) -> None:
        self._available_node = available_node
        self._pressure_unit = pressure_unit
        self._min_pressure = min_pressure
        self._max_pressure = max_pressure
        self.intializeGraphDialog()

    def intializeGraphDialog(self) -> None:
        """
        This function initializes all the graph dialog which are managed by GraphManager
        It connects signal updatePressureDataBasedOnIDSignal to all its child graph dialog
        All of the graph also connect onGraphDialogCloseSignal to onGraphDiaglogClose to inform GraphManager about its closure
        """
        self._available_graph = [GraphDialog(f"Pressure Monitoring Node {i}",i,
                                             "Time",
                                             "Pressure",
                                             self._pressure_unit,"s",
                                             self._min_pressure,
                                             self._max_pressure) for i in self._available_node]
        
        self._show_status = {i : False for i in self._available_node}
        for graph in self._available_graph:
            self.updatePressureDataBasedOnIDSignal.connect(graph.pressure_update)
            graph.onGraphDialogCloseSignal.connect(self.onGraphDiaglogClose)
        ...

    def pressureInformationUpdate(self,id : int, now : QDateTime, supply_pressure : float, target_pressure : float, output_pressure : float) -> None:
        """
        Forward pressure data to corresponding graph based on graph id
        """
        self.updatePressureDataBasedOnIDSignal.emit(id,now,supply_pressure,target_pressure,output_pressure)
        ...
    
    def showGraphBasedOnID(self,id : int) -> None:
        """
        Finding available graph based on id.
        If the graph is already being shown, it shall stop displaying another one.
        """
        for graph in self._available_graph:
            if graph._graph_id == id and not self._show_status[id]:
                graph.show()
                self._show_status[id] = True
    
    def onGraphDiaglogClose(self,id : int):
        """
        Update showing status of a graph based on graph id
        """
        self._show_status[id] = False


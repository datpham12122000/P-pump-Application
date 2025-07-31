from PySide6.QtWidgets import (QDialog, 
                               QApplication, 
                               QVBoxLayout,
                               QPushButton,
                               QCheckBox,
                               QGridLayout,
                               QSizePolicy,
                               QComboBox,
                               QLabel,
                               QLineEdit,
                               QMainWindow,
                               QWidget)
from PySide6.QtCharts import (QChart, QLineSeries, QChartView,QValueAxis, QDateTimeAxis)
from PySide6.QtGui import (QPainter, QPen, QColor)
from PySide6.QtCore import (Qt, QDateTime, Slot,QTimer, Signal,QObject, QThread)
from graph import *
from graph_manager import *
import sys
import serial
import serial.tools.list_ports as list_ports
import struct

# serial_port = 'COM4'  # Change this to your serial port
# ser = serial.Serial(serial_port, 115200, timeout=1)

class MainWindow(QMainWindow):
    displayGraphSignal = Signal(int)
    initializeInternalSignal = Signal(list,str,float,float)
    def __init__(self):
        super().__init__()
        self.serialPort = None
        self.setWindowTitle("Pressure Monitoring Tool")
        self.setGeometry(100, 100, 400, 300)

        self._graphManager = GraphManager(self)
        self._graphManager.initializeInternalVar([i for i in range (1,17)],"mbar",0.0,14000.0)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QGridLayout()
        central_widget.setLayout(layout)

        self._showGraphButton = QPushButton("Show Graph",self)
        self._showGraphButton.clicked.connect(self.onShowGraphButtonClicked)

        self._listSerialButton = QPushButton("Refresh",self)
        self._listSerialButton.clicked.connect(self.onListSerialPort)

        self._connectButton = QPushButton("Connect",self)
        self._connectButton.clicked.connect(self.onConnectSerial)

        self._selectedGraphCombobox = QComboBox(self)

        self._showAllCheckBox = QCheckBox("All",self)
        self._showAllCheckBox.setChecked(False)

        self._targetPressureLineEdit = QLineEdit(self)
        self._targetPressureLabel = QLabel("Target (mbar)")
        self._targetNodeComboBox = QComboBox(self)
        self._targetSetButton = QPushButton("Set Target")
        self._targetSetButton.clicked.connect(self.onTargetButton)

        for i in range (1,17):
            self._selectedGraphCombobox.addItem(f"Node {i}")
            self._targetNodeComboBox.addItem(f"Node {i}")
        self._serialCombobox = QComboBox(self)

        layout.addWidget(self._showGraphButton,0,0,1,2)
        layout.addWidget(self._selectedGraphCombobox,0,2,1,2)
        layout.addWidget(self._showAllCheckBox,0,4,1,2)
        layout.addWidget(self._serialCombobox,1,0,1,2)
        layout.addWidget(self._connectButton,1,2,1,2)
        layout.addWidget(self._listSerialButton,1,4,1,2)

        layout.addWidget(self._targetPressureLabel,2,0,1,3)
        layout.addWidget(self._targetPressureLineEdit,2,3,1,3)
        layout.addWidget(self._targetNodeComboBox,3,0,1,3)
        layout.addWidget(self._targetSetButton,3,3,1,3)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)

    def update_data(self):
        if self.serialPort == None:
            return
        now = QDateTime.currentDateTime()
        if self.serialPort.in_waiting >= 8:
            import struct
            byte = self.serialPort.read(8)
            supply_pressure = struct.unpack('<f', byte[:4])[0]
            output_pressure = struct.unpack('<f', byte[4:8])[0]
            self._graphManager.pressureInformationUpdate(1,now,supply_pressure,output_pressure,output_pressure)
            self._graphManager.pressureInformationUpdate(2,now,supply_pressure,output_pressure,output_pressure)
            self._graphManager.pressureInformationUpdate(3,now,supply_pressure,output_pressure,output_pressure)
            self._graphManager.pressureInformationUpdate(4,now,supply_pressure,output_pressure,output_pressure)

    def onShowGraphButtonClicked(self):
        if self._showAllCheckBox.isChecked():
            for i in range (1,17):
                self._graphManager.showGraphBasedOnID(i)
        else:
            print(self._selectedGraphCombobox.currentIndex() + 1)
            self._graphManager.showGraphBasedOnID(self._selectedGraphCombobox.currentIndex() + 1)
    
    def onListSerialPort(self):
        self._serialCombobox.clear()

        ports = list_ports.comports()
        if not ports:
            self._serialCombobox.addItem("No serial ports found")
            self._serialCombobox.setEnabled(False)
            return

        self._serialCombobox.setEnabled(True)
        for port in ports:
            desc = f"{port.device} - {port.description}"
            self._serialCombobox.addItem(desc, userData=port.device)

    def onConnectSerial(self):
        self.serialPort = serial.Serial(f"{self._serialCombobox.currentText()[:4]}",115200, timeout=1)

    def onTargetButton(self):
        try:
            target_pressure = struct.pack('<f', float(self._targetPressureLineEdit.text()))
            if self.serialPort is not None:
                self.serialPort.write(target_pressure)
                self.serialPort.flush()
                print(f"Sent {len(target_pressure)} bytes: {target_pressure.hex()}")
        except Exception as e:
            print(e)

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
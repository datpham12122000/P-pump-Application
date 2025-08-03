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
                               QWidget,QMenu,
                               QFileDialog,
                               QMessageBox
                               )
from PySide6.QtCharts import (QChart, QLineSeries, QChartView,QValueAxis, QDateTimeAxis)
from PySide6.QtGui import (QAction)
from PySide6.QtCore import (Qt, QDateTime, Slot,QTimer, Signal)
from graph import *
from graph_manager import *
import sys
import serial
import serial.tools.list_ports as list_ports
import struct
import style_sheet
import protocol_parser


class MainWindow(QMainWindow):
    displayGraphSignal = Signal(int)
    initializeInternalSignal = Signal(list,str,float,float)
    def __init__(self):
        
        super().__init__()
        self.setStyleSheet(style_sheet.main_window)
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
        
        self._showGraphButton = QPushButton("📈 Show Graph",self)
        self._showGraphButton.clicked.connect(self.onShowGraphButtonClicked)

        self._connectButton = QPushButton("🔌 Connect",self)
        self._connectButton.clicked.connect(self.onConnectSerial)

        self._selectedGraphCombobox = QComboBox(self)

        self._targetPressureLineEdit = QLineEdit(self)
        self._targetPressureLabel = QPushButton("Target (mbar)")
        self._targetPressureLabel.setEnabled(False)
        self._targetNodeComboBox = QComboBox(self)
        self._targetSetButton = QPushButton("🎯 Set Target")
        self._targetSetButton.clicked.connect(self.onTargetButton)

        for i in range (1,17):
            self._selectedGraphCombobox.addItem(f"Node {i}")
            self._targetNodeComboBox.addItem(f"Node {i}")
        self._selectedGraphCombobox.addItem(f"All Graph")
        self._serialCombobox = QComboBox(self)
# raw send widgets
        self._rawLineEdit = QLineEdit(self)
        self._rawLineEdit.setPlaceholderText("Enter raw hex, e.g. DE AD BE EF")
        self._sendRawButton = QPushButton("Send Raw", self)
        self._sendRawButton.clicked.connect(self.onSendRaw)
        self._sendRawButton.setEnabled(False)

        # place them at the bottom row (adjust row index to be below existing content)
        layout.addWidget(self._showGraphButton,0,0,1,2)
        layout.addWidget(self._selectedGraphCombobox,0,2,1,4)
        layout.addWidget(self._serialCombobox,1,2,1,4)
        layout.addWidget(self._connectButton,1,0,1,2)
        layout.addWidget(self._targetPressureLabel,2,0,1,2)
        layout.addWidget(self._targetPressureLineEdit,2,2,1,4)
        layout.addWidget(self._targetNodeComboBox,3,2,1,4)
        layout.addWidget(self._targetSetButton,3,0,1,2)
        layout.addWidget(self._rawLineEdit, 4, 2, 1, 4)
        layout.addWidget(self._sendRawButton, 4, 0, 1, 2)

        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        self._collectDataTimer = QTimer(self)
        self._collectDataTimer.timeout.connect(self.update_data)
        self._collectDataTimer.start(100)

    def onSendRaw(self):
        if self.serialPort is not None:
            text = self._rawLineEdit.text().strip()
            if not text:
                return
            cleaned = text.replace("0x", "").replace(" ", "")
            if len(cleaned) % 2 != 0:
                print("Hex string length must be even.")
                return
            try:
                raw = bytes.fromhex(cleaned)
            except ValueError as e:
                QMessageBox.critical(self,"Error","Input string is invalid",QMessageBox.Ok)
                self._rawLineEdit.clear()
                return

            try:
                self.serialPort.write(raw)
                self.serialPort.flush()
                print(f"Sent raw: {raw.hex().upper()}")
            except Exception as e:
                QMessageBox.critical(self,"Error","Fail to send data",QMessageBox.Ok)
    def update_data(self):
        """
        Update status on graph with the serial data available
        """
        if self.serialPort == None:
            return
        now = QDateTime.currentDateTime()
        if self.serialPort.in_waiting >= protocol_parser.default_frame_length:
            byte = self.serialPort.read(protocol_parser.default_frame_length)
            frame_information = protocol_parser.get_data_from_frame(byte)
            if frame_information[0] == "AtmospherePressure":
                ...
            elif frame_information[0] == "SupplyPressure":
                for i in range (1,17):
                    self._graphManager.pressureInformationUpdate(i,now,frame_information[1],-1.0,-1.0)
            elif frame_information[0] == "NodePressure":
                self._graphManager.pressureInformationUpdate(frame_information[1],now,-1.0,-1.0,frame_information[2])

    def onShowGraphButtonClicked(self):
        """
        Displaying graph based on index of selected graph combobox
        """
        if self._selectedGraphCombobox.currentIndex() + 1 == self._selectedGraphCombobox.count():
            for i in range (1,17):
                self._graphManager.showGraphBasedOnID(i)
        else:
            self._graphManager.showGraphBasedOnID(self._selectedGraphCombobox.currentIndex() + 1)
    
    def onListSerialPort(self):
        """
        List all available COM port on a combobox
        """
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
        """
        Connect to a serial port selected
        """
        if self._connectButton.text() == "🔌 Connect":
            try:
                if self._serialCombobox.count() > 0:
                    self.serialPort = serial.Serial(f"{self._serialCombobox.currentText()[:4]}",115200, timeout=1)
                    self._connectButton.setText("❌ Disconnect")
                else:
                    QMessageBox.critical(self,"Error","No port available",QMessageBox.Ok)
                    return
            except Exception as e:
                return
            self._connectButton.setText("❌ Disconnect")
            self._sendRawButton.setEnabled(True)
        else:
            self._connectButton.setText("🔌 Connect")
            self.serialPort.flush()
            self.serialPort.close()
            self._sendRawButton.setEnabled(False)
            self.serialPort = None

    def onTargetButton(self):
        """
        Send corresponding command to controller to set target pressure to a node
        """
        try:
            if self.serialPort is not None:
                node_id = self._targetNodeComboBox.currentIndex() + 1
                target_pressure = float(self._targetPressureLineEdit.text())
                command = protocol_parser.set_target_pressure(target_pressure,node_id)
                self.serialPort.write(command)
                self._graphManager.pressureInformationUpdate(node_id,QDateTime.currentDateTime(),-1.0,target_pressure,-1.0)
                self.serialPort.flush()
                # print(command.hex())
        except Exception as e:
            print(e)

    def onOpenLog(self):
        """
        Open a csv file that contain pressure data recorded 
        from previous measurement and display it on a graph
        """
        file_name, _ = QFileDialog.getOpenFileName(
        self,
        "Open Log File",
        "",
        "CSV Files (*.csv);;All Files (*)")
        if file_name:
            self._logPlayingDialog = GraphDialog(f"{file_name}",0,"Time","Pressure","s","mbar",0.0,14000.0)
            fieldnames = ["timestamp", "supply_pressure", "output_pressure", "target_pressure"]
            with open(file_name, "r") as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=fieldnames)
                for _, row in enumerate(reader, start=1):
                    timestamp_str = row["timestamp"]
                    supply_s = row["supply_pressure"]
                    output_s = row["output_pressure"]
                    target_s = row["target_pressure"]
                    self._logPlayingDialog.pressure_update(0,QDateTime.fromString(timestamp_str),
                                                           float(supply_s),
                                                           float(target_s),
                                                           float(output_s))
            self._logPlayingDialog.exec()

    def contextMenuEvent(self, event):

        menu = QMenu(self)  # optional base
        refresh_action = QAction("🔄 Refresh Serial Ports", self)
        refresh_action.triggered.connect(self.onListSerialPort)
        read_file = QAction("📂 Read a log",self)
        read_file.triggered.connect(self.onOpenLog)
        menu.addAction(refresh_action)
        menu.addAction(read_file)
        menu.exec(event.globalPos())
        
    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
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
                               QFileDialog
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

# serial_port = 'COM4'  # Change this to your serial port
# ser = serial.Serial(serial_port, 115200, timeout=1)

class MainWindow(QMainWindow):
    displayGraphSignal = Signal(int)
    initializeInternalSignal = Signal(list,str,float,float)
    def __init__(self):
        
        super().__init__()
        self.setStyleSheet("""
        QMainWindow { background: #1e1f29; }
        QWidget { font-family: "Segoe UI", system-ui; color: #e8e8f2; }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a9cff, stop:1 #3f6fc2);
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            color: white;
            font-weight: 600;
        }
        QPushButton:pressed { background: #2f5fb8; }
        QComboBox, QLineEdit {
            background: #2b2b3a;
            border: 1px solid #44475a;
            border-radius: 6px;
            padding: 4px 8px;
            min-width: 120px;
        }
        QCheckBox { padding: 2px; }
        QLabel { font-size: 12px; }
        QLabel.big { font-size: 14px; font-weight: bold; }
        QComboBox {
            background: #2b2b3a;
            color: #f0f0f8;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 6px 8px;
            font-size: 13px;
        }
        QComboBox QAbstractItemView {
            background: #1f1f2f;
            selection-background-color: #4a6fe8;
            color: #f0f0f8;
            outline: none;
        }
        QComboBox:hover {
            border: 1px solid #7faaff;
        }
        QComboBox:focus {
            border: 1px solid #9ecbff;
        }
        QMenu {
        background-color: #1f1f2f;
        color: #e8e8f2;
        border: 1px solid #555;
        padding: 4px;
        font-size: 13px;
        }
        QMenu::item {
            padding: 6px 20px;
        }
        QMenu::item:selected {
            background-color: #4a6fe8;
            color: #ffffff;
        }
        QMenu::separator {
            height: 1px;
            background: #44475a;
            margin: 5px 0;
        }
        QMenu::item:disabled {
            color: #777;
        }
        """)

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
        # self._targetPressureLabel.setAlignment(Qt.AlignCenter)  # center text inside label
        self._targetNodeComboBox = QComboBox(self)
        self._targetSetButton = QPushButton("🎯 Set Target")
        self._targetSetButton.clicked.connect(self.onTargetButton)

        for i in range (1,17):
            self._selectedGraphCombobox.addItem(f"Node {i}")
            self._targetNodeComboBox.addItem(f"Node {i}")
        self._selectedGraphCombobox.addItem(f"All Graph")
        self._serialCombobox = QComboBox(self)

        layout.addWidget(self._showGraphButton,0,0,1,3)
        layout.addWidget(self._selectedGraphCombobox,0,3,1,3)
        layout.addWidget(self._serialCombobox,1,3,1,3)
        layout.addWidget(self._connectButton,1,0,1,3)

        layout.addWidget(self._targetPressureLabel,2,0,1,3)
        layout.addWidget(self._targetPressureLineEdit,2,3,1,3)
        layout.addWidget(self._targetNodeComboBox,3,3,1,3)
        layout.addWidget(self._targetSetButton,3,0,1,3)

        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

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
        if self._selectedGraphCombobox.currentIndex() + 1 == 17:
            for i in range (1,17):
                self._graphManager.showGraphBasedOnID(i)
        else:
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
    def onOpenLog(self):
        file_name, _ = QFileDialog.getOpenFileName(
        self,
        "Open Log File",
        "",                          # start directory
        "CSV Files (*.csv);;All Files (*)"
    )
        if file_name:
            self._logPlayingDialog = GraphDialog(f"{file_name}",0,"Time","Pressure","s","mbar",0.0,14000.0)
            fieldnames = ["timestamp", "supply_pressure", "output_pressure", "target_pressure"]
            with open(file_name, "r") as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=fieldnames)
                for row_idx, row in enumerate(reader, start=1):
                    timestamp_str = row["timestamp"]
                    supply_s = row["supply_pressure"]
                    output_s = row["output_pressure"]
                    target_s = row["target_pressure"]
                    self._logPlayingDialog.pressure_update(0,QDateTime.fromString(timestamp_str),
                                                           float(supply_s),
                                                           float(output_s),
                                                           float(target_s))
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
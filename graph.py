from PySide6.QtWidgets import QDialog, QApplication, QVBoxLayout,QPushButton,QCheckBox,QGridLayout,QSizePolicy,QGraphicsLineItem,QLabel
from PySide6.QtCharts import QChart, QLineSeries, QChartView,QValueAxis, QDateTimeAxis
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QDateTime, Slot,QTimer, Signal
import serial
import sys
# for testing purposes only, shall be refactored later
serial_port = 'COM4'  # Change this to your serial port
ser = serial.Serial(serial_port, 115200, timeout=1)

class CustomChartView(QChartView):
    """
    Custom chart view to handle mouse events and provide a customed featured chart.
    This class inherits from QChartView and provides additional functionality for panning, zooming,
    """

    TargetPressureCursorSignal = Signal(str,float)
    OutputPressureCursorSignal = Signal(str,float)
    SupplyPressureCursorSignal = Signal(str,float)

    def __init__(self,graph_name: str,
                 x_axis_label: str,
                 y_axis_label: str,
                 x_axis_unit: str = "",
                 y_axis_unit: str = "",
                 min_y_range: float = 0.0,
                 max_y_range: float = 100.0,
                 parent=None):
        
        
        self._chartFreeze = False
        """
        Set the maximum range of y-axis to be displayed on the chart.
        """

        self._min_y_range = min_y_range
        self._max_y_range = max_y_range

        """ 
        These 2 variables below are used to determine if the chart is currently being panned with the mouse.
        _chartPanning is set to True when the left mouse button is pressed and False when it is released.
        _lastMousePos is used to store the last mouse position when the left button is pressed
        """
        self._chartPanning = False
        self._lastMousePos = None

        """
        Initialize the chart view with a chart and set up the axes and series.
        """
        self._chartPressure = QChart()
        self._chartPressure.setTitle(graph_name)

        super().__init__(self._chartPressure, parent)

        """
        These 2 variables to store status of the cursor.
        _cursorEnabled is used to determine if the cursor is enabled or not.
        _pivotTheCursor is used to determine if the cursor should follow the mouse position or not.
        When the cursor is enabled, a vertical line will be drawn on mouse move.
        """
        self._cursorEnabled = True
        self._pivotTheCursor = False
        # Vertical line to be drawn on mouse move
        """
        Create a vertical line to be drawn on mouse move.
        This line will be used to indicate the current position of the cursor on the chart.
        """
        self._vline = QGraphicsLineItem()
        self._vline.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        
        """
        Add the vertical line to the chart scene.
        This allows the line to be drawn on the chart when the cursor is enabled.
        """
        self.scene().addItem(self._vline)

        """
        Create line series for supply pressure, output pressure, and target pressure.
        The displayed line in the chart shall represent by the data added to the series.
        Each series is given a name for identification.
        """

        # --- Supply pressure ---
        self._supplyPressureLineSeries = QLineSeries()
        self._supplyPressureLineSeries.setName("Supply Pressure")

        # --- Output pressure ---
        self._outputPressureSeries = QLineSeries()
        self._outputPressureSeries.setName("Output Pressure")

        # --- Target pressure ---
        self._targetPressureSeries = QLineSeries()
        self._targetPressureSeries.setName("Target Pressure")

        """ 
        Add all series to the chart.
        This allows the chart to display multiple lines representing different data series.
        """
        # Add all series to chart
        self._chartPressure.addSeries(self._supplyPressureLineSeries)
        self._chartPressure.addSeries(self._outputPressureSeries)
        self._chartPressure.addSeries(self._targetPressureSeries)

        # Add axis labels to the chart
        """
        Create x-axis and y-axis for the chart.
        The x-axis is a date-time axis, and the y-axis is a value axis.
        """
        # X-axis
        self._x_axis = QDateTimeAxis()
        self._x_axis.setFormat("hh:mm:ss")
        self._x_axis.setTitleText(x_axis_label + " (" + x_axis_unit + ")")
        self.time_since_start = QDateTime.currentDateTime()
        self._x_axis.setMin(self.time_since_start) 
        self._x_axis.setMax(self.time_since_start.addSecs(10))  # Set initial range to 10 seconds

        # Tick count is the number that the whole x-axis is divided into.
        # This is used to determine how many ticks are shown on the x-axis.
        self._x_axis.setTickCount(11)

        # Y-axis
        self._y_axis = QValueAxis()
        self._y_axis.setTitleText(y_axis_label + " (" + y_axis_unit + ")")
        self._y_axis.setTickCount(11)

        # Set the range of the y-axis based on the provided min and max values
        # With tick count set to 11 and min_y_range = 0, max_y_range = 100 for instance,
        # this will create a range that is divided into 10 equal parts.
        # These ranges are displayed on the y-axis as follows:
        # 0 - 10, 10 - 20, 20 - 30, 30 - 40, 40 - 50, 50 - 60, 60 - 70, 70 - 80, 80 - 90, 90 - 100
        self._y_axis.setRange(min_y_range, max_y_range)

        # Add x-axis to the chart
        self._chartPressure.addAxis(self._x_axis, Qt.AlignBottom)

        # Attach x axes to series
        # This allows the series to be displayed on the x-axis of the chart.
        self._supplyPressureLineSeries.attachAxis(self._x_axis)
        self._outputPressureSeries.attachAxis(self._x_axis)
        self._targetPressureSeries.attachAxis(self._x_axis)

        # Attach y axes to series
        self._chartPressure.addAxis(self._y_axis, Qt.AlignLeft)

        # Attach y axes to series
        # This allows the series to be displayed on the y-axis of the chart.
        self._supplyPressureLineSeries.attachAxis(self._y_axis)
        self._outputPressureSeries.attachAxis(self._y_axis)
        self._targetPressureSeries.attachAxis(self._y_axis)

    def find_closest_point(self, x , series: QLineSeries) -> int:
        """
        Find the closest point in the series to the given x-coordinate.
        This is used to determine the position of the vertical line on mouse move.
        """
        closest_index = 0
        min_distance = float('inf')
        for i in range(series.count()):
            point = series.at(i)
            distance = abs(point.x() - x)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        return closest_index
    
    def wheelEvent(self, event):
        """
        Zooming or out is just about changing the range displayed on the x-axis.
        This is done by changing the min and max values of the x-axis based on the mouse wheel event.
        """
        zoom_factor = 1.2
        if event.angleDelta().y() < 0:
            zoom_factor = 1 / zoom_factor
            self._chartPressure.zoom(zoom_factor)
        else:
            zoom_factor = zoom_factor
            self._chartPressure.zoom(zoom_factor)
        super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        """
        Handle mouse press events to enable or disable the cursor.
        If the cursor is enabled, a vertical line will be drawn on mouse move.
        This is also used to handler pan the chart.
        """
        if self._cursorEnabled:
            if event.button() == Qt.LeftButton:
                self._pivotTheCursor = True
            elif event.button() == Qt.RightButton:
                self._pivotTheCursor = False
        if event.button() == Qt.LeftButton:
            self._chartPanning = True
            self._lastMousePos = event.position().toPoint()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events to update the vertical line position.
        If the pivot cursor is not set, the vertical line will follow the mouse cursor.
        """
        if self._cursorEnabled:
            pos = event.position().toPoint()
            if self._cursorEnabled and self.chart().plotArea().contains(pos):
                if not self._pivotTheCursor:
                    self._vline.setLine(pos.x(), self.chart().plotArea().top(), pos.x(), self.chart().plotArea().bottom())
                    series_pos = self.chart().mapToValue(pos)

                    if self._supplyPressureLineSeries.count() > 0:
                        closest_point_supply_pressure = self.find_closest_point(series_pos.x(), self._supplyPressureLineSeries)
                        self.SupplyPressureCursorSignal.emit("supply",self._supplyPressureLineSeries.at(closest_point_supply_pressure).y())

                    if self._outputPressureSeries.count() > 0:
                        closest_point_output_pressure = self.find_closest_point(series_pos.x(), self._outputPressureSeries)
                        self.OutputPressureCursorSignal.emit("output",self._outputPressureSeries.at(closest_point_output_pressure).y())

                    if self._targetPressureSeries.count() > 0:
                        closest_point_target_pressure = self.find_closest_point(series_pos.x(), self._targetPressureSeries)
                        self.TargetPressureCursorSignal.emit("target",self._targetPressureSeries.at(closest_point_target_pressure).y())

        """
        In case move event is used to pan the chart, the chart will scroll horizontally based on the mouse movement.
        """
        if self._chartPanning and self._lastMousePos is not None:
            delta = event.position().toPoint() - self._lastMousePos
            self._chartPressure.scroll(-delta.x(), 0)
            self._lastMousePos = event.position().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events to stop panning the chart.
        If the left button is released, the chart panning will stop.
        """
        if event.button() == Qt.LeftButton:
            self._chartPanning = False
            self._lastMousePos = None
        super().mouseReleaseEvent(event)

    @Slot(QDateTime, float)
    def add_supply_pressure_data(self, timestamp: QDateTime, value: float):
        """
        Add a new data point to the supply pressure series.
        This is also a slot that can be connected to a signal to update the series with new data.
        Because the x-axis is a date-time axis, the timestamp is used to determine the position of the data point on the x-axis.
        setMin and setMax are used to adjust the x-axis range based on the new data point.
        timestamp.AddSecs(-10) is used to make sure that the x-axis range shall display the last 10 seconds of data
        """
        if self._supplyPressureLineSeries.count() > 1 and not self._chartFreeze:
            self._x_axis.setMin(max(timestamp.addSecs(-10),self.time_since_start))
            self._x_axis.setMax(max(timestamp, self.time_since_start.addSecs(10)))
        self._supplyPressureLineSeries.append(timestamp.toMSecsSinceEpoch(), value)

    @Slot(QDateTime, float) 
    def add_output_pressure_data(self, timestamp: QDateTime, value: float):
        """
        Add a new data point to the output pressure series.
        This is also a slot that can be connected to a signal to update the series with new data.
        Because the x-axis is a date-time axis, the timestamp is used to determine the position of the data point on the x-axis.
        setMin and setMax are used to adjust the x-axis range based on the new data point.
        timestamp.AddSecs(-10) is used to make sure that the x-axis range shall display the last 10 seconds of data
        """
        if self._outputPressureSeries.count() > 1 and not self._chartFreeze:
            self._x_axis.setMin(max(timestamp.addSecs(-10),self.time_since_start))
            self._x_axis.setMax(max(timestamp, self.time_since_start.addSecs(10)))
        self._outputPressureSeries.append(timestamp.toMSecsSinceEpoch(), value)

    @Slot(QDateTime, float)
    def add_target_pressure_data(self, timestamp: QDateTime, value: float):
        """
        Add a new data point to the target pressure series.
        This is also a slot that can be connected to a signal to update the series with new data.
        Because the x-axis is a date-time axis, the timestamp is used to determine the position of the data point on the x-axis.
        setMin and setMax are used to adjust the x-axis range based on the new data point.
        timestamp.AddSecs(-10) is used to make sure that the x-axis range shall display the last 10 seconds of data
        """
        if self._targetPressureSeries.count() > 1 and not self._chartFreeze:
            self._x_axis.setMin(max(timestamp.addSecs(-10),self.time_since_start))
            self._x_axis.setMax(max(timestamp, self.time_since_start.addSecs(10)))
        self._targetPressureSeries.append(timestamp.toMSecsSinceEpoch(), value)

    @Slot()
    def hold_chart(self):
        """
        Slot to hold the chart, which can be connected to a button click signal.
        This can be used to pause the chart updates. By updating the _chartFreeze variable,
        the chart will not update horizontal axis when new data is added.
        """
        self._chartFreeze = True

    @Slot()
    def resume_chart(self):
        """
        Slot to resume the chart, which can be connected to a button click signal.
        This can be used to resume the chart updates after holding it.
        when the chart is resumed, the _chartFreeze variable is set to False,
        allowing the chart to update with new data.
        """
        self._y_axis.setRange(self._min_y_range,self._max_y_range)
        self._chartFreeze = False

    @Slot(bool)
    def set_cursor_enabled(self, enabled: bool):
        """
        Slot to enable or disable the cursor.
        This can be connected to a checkbox state change signal.
        When enabled, the cursor will show a vertical line on mouse move.
        """
        self._cursorEnabled = enabled
        if not enabled:
            self._vline.setLine(0, 0, 0, 0)
        else:
            self._vline.setLine(self.chart().plotArea().left(), self.chart().plotArea().top(), self.chart().plotArea().left(), self.chart().plotArea().bottom())

    @Slot(int)
    def toggle_sampling(self ,state :int):
        """
        Slot to toggle the sampling of the chart, which can be connected to a checkbox state change signal.
        This can be used to enable or disable the sampling of the chart data.
        """
        self._supplyPressureLineSeries.setPointsVisible(state != 0)
        self._outputPressureSeries.setPointsVisible(state != 0)
        self._targetPressureSeries.setPointsVisible(state != 0)

    @Slot(int)
    def toggle_rendering(self, state: int):
        """
        Slot to toggle the rendering of the chart, which can be connected to a checkbox state change signal.
        This can be used to enable or disable the rendering of the chart data points.
        """
        self.setRenderHints(QPainter.Antialiasing if state != 0 else QPainter.RenderHints())

class GraphDialog(QDialog):

    """
    This class is used to create a window that displays a graph with 3 lines intended to show supply pressure, output pressure, and target pressure.
    The graph is created using PySide6's QChart and QLineSeries classes.
    For general creation of a graph, the class takes parameters for the graph name, x-axis label, y-axis label, and optional units for both axes.
    """

    def __init__(self, graph_name: str, 
                 x_axis_label: str, 
                 y_axis_label: str , 
                 x_axis_unit: str = "", 
                 y_axis_unit: str = "",
                 min_y_range: float = 0.0,
                 max_y_range: float = 100.0):
        super().__init__()

        self._chartFreeze = False
        """ Initialize the dialog window with a title and layout. """
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(graph_name)

        """
        Set the size of the dialog window.
        """
        self.resize(700, 500)

        """
        Create a chart view to display the chart.
        The chart view is responsible for rendering the chart and its series.
        """
        self._chartView = CustomChartView(graph_name,x_axis_label, y_axis_label, x_axis_unit, y_axis_unit, min_y_range, max_y_range,self);
        self._chartView.TargetPressureCursorSignal.connect(self.display_pressure_data)
        self._chartView.OutputPressureCursorSignal.connect(self.display_pressure_data)
        self._chartView.SupplyPressureCursorSignal.connect(self.display_pressure_data)
        """ 
        Finally add the chart view widget to the dialog layout 
        """
        self.layout.addWidget(self._chartView)

        """ 
        Add related buttons to the dialog layout 
        """
        # Add a layout for the buttons and other controls
        self._controlLayout = QGridLayout(self)
        # Add a button to hold the chart
        self._holdButton = QPushButton("Hold",self)
        self._holdButton.clicked.connect(self._chartView.hold_chart)
        # Add a button to resume the chart
        self._resumeButton = QPushButton("Resume",self)
        self._resumeButton.clicked.connect(self._chartView.resume_chart)
        # Add a checkbox to toggle sampling
        self._samplingCheckBox = QCheckBox("Sampling",self)
        self._samplingCheckBox.stateChanged.connect(self._chartView.toggle_sampling)
        # Add a checkbox to toggle rendering of points
        self._renderingCheckBox = QCheckBox("Render Points",self)
        self._renderingCheckBox.stateChanged.connect(self._chartView.toggle_rendering)
        # Add a checkbox to enable or disable the cursor
        self._cursorCheckBox = QCheckBox("Enable Cursor",self)
        self._cursorCheckBox.setChecked(True)
        self._cursorCheckBox.stateChanged.connect(self._chartView.set_cursor_enabled)

        self._outputPressureLabel = QLabel("Output Pressure: ",self)
        self._outputPressureLabel.setText("Output Pressure: n/a mbar")
        self._targetPressureLabel = QLabel("Target Pressure: ",self)
        self._targetPressureLabel.setText("Target Pressure: n/a mbar")
        self._supplyPressureLabel = QLabel("Supply Pressure: ",self)
        self._supplyPressureLabel.setText("Supply Pressure: n/a mbar")
      # Add the buttons and checkbox to the layout
        self._controlLayout.addWidget(self._holdButton, 0, 0, 1, 2)
        self._controlLayout.addWidget(self._resumeButton, 0, 2, 1, 2)
        self._controlLayout.addWidget(self._outputPressureLabel, 1, 0, 1, 2)
        self._controlLayout.addWidget(self._targetPressureLabel, 1, 2, 1, 2)
        self._controlLayout.addWidget(self._supplyPressureLabel, 1, 4, 1, 2)
        self._controlLayout.addWidget(self._samplingCheckBox, 2, 0, 2, 2)
        self._controlLayout.addWidget(self._renderingCheckBox, 2, 2, 2, 2)
        self._controlLayout.addWidget(self._cursorCheckBox, 2, 4, 2, 2)
        self.layout.addLayout(self._controlLayout)

        self.setLayout(self.layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    @Slot(str,float)
    def display_pressure_data(self,name:str, value: float):
        """
        Slot to display supply pressure data on the chart in which the cursor is currently positioned.
        """
        print(f"name: {name}, value: {value}")
        if name == "supply":
            self._supplyPressureLabel.setText(f"Supply Pressure: {value} mbar")
        elif name == "output":
            self._outputPressureLabel.setText(f"Output Pressure: {value} mbar")
        elif name == "target":
            self._targetPressureLabel.setText(f"Target Pressure: {value} mbar")

    @Slot()
    def update_data(self):
        # for testing purposes only, shall be refactored later
        # this slot will be connected to a graph manager that will update the chart with new data
        global ser
        now = QDateTime.currentDateTime()
        if ser.in_waiting > 0:
            byte = ser.read(8)
            supply_pressure = byte[0] << 24 | byte[1] << 16 | byte[2] << 8 | byte[3]
            output_pressure = byte[4] << 24 | byte[5] << 16 | byte[6] << 8 | byte[7]
            self._chartView.add_supply_pressure_data(now, supply_pressure)
            self._chartView.add_output_pressure_data(now, output_pressure)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = GraphDialog("Pressure Monitoring Chart Node", "Time", "Value" ,"s", "mbar",0.0,14000.0)
    dialog.exec()

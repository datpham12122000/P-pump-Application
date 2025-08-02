from PySide6.QtWidgets import (QDialog, QApplication, QVBoxLayout,
                               QPushButton,QCheckBox,QGridLayout
                               ,QSizePolicy,QGraphicsLineItem,QLabel)

from PySide6.QtCharts import (QChart, QLineSeries, QChartView,
                              QValueAxis, QDateTimeAxis)

from PySide6.QtGui import (QPainter, QPen, QColor,QFont,QLinearGradient)

from PySide6.QtCore import (Qt, QDateTime, Slot,QTimer, 
                            Signal)
import csv
import style_sheet

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
        
        self._firstTimeInsertData = True
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
        self._chartPressure.setTitleBrush(QColor("white"))   # set text color
        self._chartPressure.setTitleFont(QFont("Segoe UI", 9, QFont.Bold))
        self._chartPressure.setBackgroundBrush(QColor(30, 31, 41))  # dark slate

        # Plot area background (behind the series)
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(25, 26, 36))
        gradient.setColorAt(1.0, QColor(35, 36, 50))
        self._chartPressure.setPlotAreaBackgroundBrush(gradient)
        self._chartPressure.setPlotAreaBackgroundVisible(True)
        legend = self._chartPressure.legend()
        legend.setLabelColor(QColor("white"))

        for axis in self._chartPressure.axes():
            axis.setLabelsBrush(QColor("white"))
            axis.setTitleBrush(QColor("white"))
            axis.setGridLineVisible(True)
            # Optional: lighter grid lines
            if hasattr(axis, "setGridLineColor"):
                axis.setGridLineColor(QColor(80, 80, 100))
            # Tick lines etc.
            axis.setLabelsFont(QFont("Segoe UI", 9))

        super().__init__(self._chartPressure, parent)

        """
        These 2 variables to store status of the cursor.
        _cursorEnabled is used to determine if the cursor is enabled or not.
        _pivotTheCursor is used to determine if the cursor should follow the mouse position or not.
        When the cursor is enabled, a vertical line will be drawn on mouse move.
        """
        self._cursorEnabled = False
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
        
        self._supplyPressureLineSeries.setPen(QPen(QColor("#FFFF00"), 2))     # light cyan
        self._outputPressureSeries.setPen(QPen(QColor("#1E90FF"), 2))     # amber
        self._targetPressureSeries.setPen(QPen(QColor("#50fa7b"), 2))
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
        self._y_axis.setTickCount(15)

        # Set the range of the y-axis based on the provided min and max values
        # With tick count set to 11 and min_y_range = 0, max_y_range = 100 for instance,
        # this will create a range that is divided into 10 equal parts.
        # These ranges are displayed on the y-axis as follows:
        # 0 - 10, 10 - 20, 20 - 30, 30 - 40, 40 - 50, 50 - 60, 60 - 70, 70 - 80, 80 - 90, 90 - 100
        self._y_axis.setRange(min_y_range, max_y_range)

        white = QColor("white")
        self._x_axis.setLabelsBrush(white)
        self._x_axis.setTitleBrush(white)
        self._x_axis.setLabelsFont(QFont("Segoe UI", 9))
        self._x_axis.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))

        self._y_axis.setLabelsBrush(white)
        self._y_axis.setTitleBrush(white)
        self._y_axis.setLabelsFont(QFont("Segoe UI", 9))
        self._y_axis.setTitleFont(QFont("Segoe UI", 10, QFont.Bold))
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

        self.setRenderHints(QPainter.Antialiasing)


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
        We find the center of the current range by adding min and max value then divide it by 2 , take the interger part
        If it is zooming in, we set new duration by half of current duration and vice versa
        Finally, we set new min and max value of x-axis range calculated by addition and minus its current center by half of new duration
        """
        if event.angleDelta().y() < 0:
            min_time = self._x_axis.min()
            max_time = self._x_axis.max()
            duration = min_time.msecsTo(max_time)
            center = min_time.addMSecs(duration // 2)
            new_duration = duration * 2
            self._x_axis.setMin(center.addMSecs(-int(new_duration // 2)))
            self._x_axis.setMax(center.addMSecs(int(new_duration // 2)))
        else:
            min_time = self._x_axis.min()
            max_time = self._x_axis.max()
            duration = min_time.msecsTo(max_time)
            center = min_time.addMSecs(duration // 2)
            new_duration = duration * 0.5
            self._x_axis.setMin(center.addMSecs(-int(new_duration // 2)))
            self._x_axis.setMax(center.addMSecs(int(new_duration // 2)))
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
        """
        if self._firstTimeInsertData:
            self._x_axis.setMin(timestamp)
            self._x_axis.setMax(timestamp.addSecs(30))
            self._firstTimeInsertData = False
        self._supplyPressureLineSeries.append(timestamp.toMSecsSinceEpoch(), value)
        if not self._cursorEnabled:
            self.SupplyPressureCursorSignal.emit("supply",value)

    @Slot(QDateTime, float) 
    def add_output_pressure_data(self, timestamp: QDateTime, value: float):
        """
        Add a new data point to the output pressure series.
        This is also a slot that can be connected to a signal to update the series with new data.
        """
        if self._firstTimeInsertData:
            self._x_axis.setMin(timestamp)
            self._x_axis.setMax(timestamp.addSecs(30))
            self._firstTimeInsertData = False
        self._outputPressureSeries.append(timestamp.toMSecsSinceEpoch(), value)
        if not self._cursorEnabled:
            self.OutputPressureCursorSignal.emit("output",value)

    @Slot(QDateTime, float)
    def add_target_pressure_data(self, timestamp: QDateTime, value: float):
        """
        Add a new data point to the target pressure series.
        This is also a slot that can be connected to a signal to update the series with new data.
        """
        if self._firstTimeInsertData:
            self._x_axis.setMin(timestamp)
            self._x_axis.setMax(timestamp.addSecs(30))
            self._firstTimeInsertData = False
        self._targetPressureSeries.append(timestamp.toMSecsSinceEpoch(), value)
        if not self._cursorEnabled:
            self.TargetPressureCursorSignal.emit("target",value)

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

class GraphDialog(QDialog):

    """
    This class is used to create a window that displays a graph with 3 lines intended to show supply pressure, output pressure, and target pressure.
    The graph is created using PySide6's QChart and QLineSeries classes.
    For general creation of a graph, the class takes parameters for the graph name, x-axis label, y-axis label, and optional units for both axes.
    """
    onGraphDialogCloseSignal = Signal(int)
    def __init__(self, graph_name: str,
                 graph_id : int,
                 x_axis_label: str, 
                 y_axis_label: str , 
                 x_axis_unit: str = "", 
                 y_axis_unit: str = "",
                 min_y_range: float = 0.0,
                 max_y_range: float = 100.0,
                 parent = None):
        
        super().__init__(parent)
        self._node_available = False
        self.setStyleSheet(style_sheet.graph_dialog_style_sheet)
        self._logdata = list()
        self._logSaving = False
        self._chartFreeze = False

        """ Initialize the dialog window with a title and layout. """
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(graph_name)
        self.graph_name = graph_name
        self._graph_id = graph_id
        """
        Set the size of the dialog window.
        """
        self.resize(1000, 700)

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
        self._controlLayout = QGridLayout(self)

        # Add a button to saving log
        self._logSavingButton = QPushButton("Save",self)
        self._logSavingButton.clicked.connect(self.log_saving)

        # Add a checkbox to toggle sampling
        self._samplingCheckBox = QCheckBox("Sampling",self)
        self._samplingCheckBox.stateChanged.connect(self._chartView.toggle_sampling)
        # Add a checkbox to enable or disable the cursor
        self._cursorCheckBox = QCheckBox("Enable Cursor",self)
        self._cursorCheckBox.setChecked(False)
        self._cursorCheckBox.stateChanged.connect(self._chartView.set_cursor_enabled)

        self._outputPressureLabel = QLabel("Output Pressure: ",self)
        self._outputPressureLabel.setText("Output Pressure: n/a mbar")
        self._targetPressureLabel = QLabel("Target Pressure: ",self)
        self._targetPressureLabel.setText("Target Pressure: n/a mbar")
        self._supplyPressureLabel = QLabel("Supply Pressure: ",self)
        self._supplyPressureLabel.setText("Supply Pressure: n/a mbar")

        self._supplyPressureLabel.setStyleSheet(f"color: {self._chartView._supplyPressureLineSeries.pen().color().name()};")
        self._outputPressureLabel.setStyleSheet(f"color: {self._chartView._outputPressureSeries.pen().color().name()};")
        self._targetPressureLabel.setStyleSheet(f"color: {self._chartView._targetPressureSeries.pen().color().name()};")
      # Add the buttons and checkbox to the layout
        self._controlLayout.addWidget(self._outputPressureLabel, 0, 0, 1, 2)
        self._controlLayout.addWidget(self._targetPressureLabel, 0, 2, 1, 2)
        self._controlLayout.addWidget(self._supplyPressureLabel, 0, 4, 1, 2)
        self._controlLayout.addWidget(self._samplingCheckBox, 1, 0, 1, 2)
        self._controlLayout.addWidget(self._cursorCheckBox, 1, 2, 1, 2)
        self._controlLayout.addWidget(self._logSavingButton, 1, 4, 1, 2)
        self.layout.addLayout(self._controlLayout)

        self.setLayout(self.layout)

    def closeEvent(self, event):
        """
        Action needed before closing
        Saving logging data still in the buffer to the file
        Notifying GraphManager about its closure
        """
        if self._logSaving:
            self.save_logging_data()
        self.onGraphDialogCloseSignal.emit(self._graph_id)
        super().closeEvent(event)
    
    @Slot()
    def log_saving(self) -> None:

        """
        Slot to turn on/off saving log feature
        """
        self._logSaving = not self._logSaving
        self._logSavingButton.setText("Saving..." if self._logSaving else "Save")

        if self._logSaving is False and len(self._logdata):
            self.save_logging_data()

    @Slot(str,float)
    def display_pressure_data(self,name:str, value: float) -> None:
        """
        Slot to display supply pressure data on the chart in which the cursor is currently positioned.
        """
        if name == "supply":
            self._supplyPressureLabel.setText(f"Supply Pressure: {format(value,".2f")} mbar")
        elif name == "output":
            self._outputPressureLabel.setText(f"Output Pressure: {format(value,".2f")} mbar")
        elif name == "target":
            self._targetPressureLabel.setText(f"Target Pressure: {format(value,".2f")} mbar")

    @Slot(QDateTime,float,float,float)
    def pressure_update(self,id_: int, now: QDateTime,
                        supply_pressure : float, 
                        target_pressure : float, 
                        output_pressure : float ) -> None:
        """
        This slot is used to update pressure data in official version
        It shall be connected to graph_manager.py which shall feed the real time data for each node corresponding to its graph diaglog
        If saving is enabled, it shall automatically save to a file after 1000 samples to reduce number of time we have to open/close 
        the file for saving workload purpose
        If pressure value is less than 0 then this value has no update
        """
        if self._graph_id != id_:
            return
        if supply_pressure >= 0.0 and self._node_available:
            self._chartView.add_supply_pressure_data(now, supply_pressure)
        if output_pressure >= 0.0:
            self._chartView.add_output_pressure_data(now, output_pressure)
            self._node_available = True
        if target_pressure >= 0.0 and self._node_available:
            self._chartView.add_target_pressure_data(now, target_pressure)
        

        if self._logSaving:
            self._logdata.append([now.toString(),
                        str(format(supply_pressure,".2f")),
                        str(format(output_pressure,".2f")),
                        str(format(target_pressure,".2f"))])
            if len(self._logdata) >= 1000:
                self.save_logging_data()

    def save_logging_data(self) -> None:
        try:
            with open(f"{self.graph_name}.csv",'a') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(self._logdata)
            self._logdata.clear()
        except Exception as e:
            print(e)

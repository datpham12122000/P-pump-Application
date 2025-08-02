# Pressure Monitoring Tool

This project is a desktop application for monitoring and logging pressure data from multiple nodes via a serial connection. It provides real-time graph visualization, target pressure setting, and CSV data logging, all built with PySide6 (Qt for Python).

## Features

- **Serial Communication:** Connect to and read data from pressure sensors via a serial port.
- **Multi-Node Support:** Monitor up to 16 nodes simultaneously.
- **Real-Time Graphs:** Visualize supply, output, and target pressures for each node.
- **Target Pressure Control:** Set and send target pressures to individual nodes.
- **Data Logging:** Save pressure data to CSV files for later analysis.
- **User-Friendly GUI:** Intuitive interface with controls for connection, graph display, and logging.

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/pump-app.git
   cd pump-app
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. **Connect your pressure sensors** to your PC via the appropriate serial port.
2. **Run the application:**
   ```sh
   python main.py
   ```
3. **Select the serial port** and click "Connect".
4. **Choose a node** and click "Show Graph" to visualize its data.
5. **Set target pressures** and log data as needed.

## File Structure

- main.py — Main application window and logic.
- graph_manager.py — Manages multiple graph dialogs and data routing.
- graph.py — Graph dialog and chart logic.
- requirements.txt — Python dependencies.

## Requirements

- Python 3.8+
- PySide6 6.9.1
- pyserial 3.5

## Notes

- Ensure your user account has permission to access the serial port and write files.
- Data is saved as CSV files named after each node/graph.

---

**Developed by DatPham**  
For questions or contributions, please open an issue or pull request.

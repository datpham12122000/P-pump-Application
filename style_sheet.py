main_window = """
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
        """
graph_dialog_style_sheet = """
        QDialog {
            background: #1f1f29;
            color: #e8e8f2;
            font-family: "Segoe UI", system-ui;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5a9cff, stop:1 #3f6fc2);
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            color: white;
            font-weight: 600;
        }
        QPushButton:pressed { background: #2f5fb8; }
        QCheckBox { padding: 2px; }
        QLabel { font-size: 12px; }
        QLabel, QCheckBox {
            color: white;
            font-size: 12px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #777;
            border-radius: 4px;
            background: #2b2b3a;
        }

        /* Checked state: bright background so the check is visible */
        QCheckBox::indicator:checked {
            background: #5a9cff;
            border: 1px solid #5a9cff;
        }
        QChartView {
            background: transparent;
            border: none;
        }
        """
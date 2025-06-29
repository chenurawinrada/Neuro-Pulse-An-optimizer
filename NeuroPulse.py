import os
import sys
import math
import psutil
import ctypes
import gc
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QGraphicsDropShadowEffect,
    QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon

class CyberpunkMonitor(QWidget):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(240, 100)
        self.move(100, 100)

        # Background label
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 240, 100)
        self.bg_label.setStyleSheet("""
            background-color: rgba(10, 10, 30, 180);
            border: 2px solid #FF00FF;
            border-radius: 12px;
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor("#FF00FF"))
        shadow.setOffset(0)
        self.bg_label.setGraphicsEffect(shadow)

        # CPU/MEM text label
        self.text_label = QLabel(self)
        self.text_label.setFont(QFont('Consolas', 11, QFont.Bold))
        self.text_label.setStyleSheet("color: #00FFFF;")
        self.text_label.setGeometry(60, 25, 170, 50)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Lightning icon
        self.lightning_icon = QLabel("⚡", self)
        self.lightning_icon.setFont(QFont('Consolas', 10))
        self.lightning_icon.setStyleSheet("color: #00FFFF; background: transparent;")
        self.lightning_icon.setFixedSize(32, 32)
        self.lightning_icon.move(15, 15)

        # Brain icon
        self.brain_icon = QLabel("🧠", self)
        self.brain_icon.setFont(QFont('Consolas', 10))
        self.brain_icon.setStyleSheet("color: #00FFFF; background: transparent;")
        self.brain_icon.setFixedSize(32, 32)
        self.brain_icon.move(14, 44)

        # Close button (hidden initially)
        self.close_button = QLabel("✖", self)
        self.close_button.setFont(QFont("Consolas", 10, QFont.Bold))
        self.close_button.setStyleSheet("""
            QLabel {
                color: #FF0055;
                background-color: rgba(30, 0, 0, 200);
                border-radius: 6px;
                padding: 2px;
            }
            QLabel:hover {
                background-color: rgba(255, 0, 80, 220);
            }
        """)
        self.close_button.setFixedSize(20, 20)
        self.close_button.move(self.width() - 26, 6)
        self.close_button.setAlignment(Qt.AlignCenter)
        self.close_button.mousePressEvent = self.close_widget
        self.close_button.hide()

        # Optimize memory button
        self.optimize_button = QLabel("⚙", self)
        self.optimize_button.setFont(QFont("Consolas", 12))
        self.optimize_button.setStyleSheet("""
            QLabel {
                color: #00FF88;
                background-color: rgba(0, 30, 0, 180);
                border-radius: 6px;
                padding: 2px;
            }
            QLabel:hover {
                background-color: rgba(0, 255, 140, 200);
            }
        """)
        self.optimize_button.setFixedSize(20, 20)
        self.optimize_button.move(self.width() - 40, (self.height() - 20)//2)
        self.optimize_button.setAlignment(Qt.AlignCenter)
        self.optimize_button.mousePressEvent = lambda e: self.optimize_memory()
        self.optimize_button.show()

        # Pulse animation
        self.pulse_min = 12
        self.pulse_max = 14
        self.pulse_step = 0.2
        self.pulse_current = self.pulse_min
        self.pulse_growing = True

        self.pulse_timer = QTimer()
        self.pulse_timer.setInterval(30)
        self.pulse_timer.timeout.connect(self.pulse_font_size)
        self.optimize_button.installEventFilter(self)

        # Close button auto-hide
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.close_button.hide)

        self.old_pos = None

        # Icon wave animation
        self.wave_duration = 1000
        self.wave_timer = QTimer()
        self.wave_timer.setInterval(30)
        self.wave_timer.timeout.connect(self.animate_wave)
        self.wave_elapsed = 0
        self.waving = False

        self.trigger_wave_timer = QTimer()
        self.trigger_wave_timer.setInterval(5000)
        self.trigger_wave_timer.timeout.connect(self.start_wave)
        self.trigger_wave_timer.start()

        # Neon border
        self.neon_hue = 180
        self.neon_direction = 1
        self.neon_timer = QTimer()
        self.neon_timer.setInterval(30)
        self.neon_timer.timeout.connect(self.animate_neon_border)
        self.neon_timer.start()

        # Update metrics
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1500)

        self.update_metrics()

        # System tray
        icon_path = os.path.join(os.path.dirname(__file__), "MemCPUApp.ico")
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip("Cyberpunk Monitor")

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        optimize_action = QAction("Optimize Now", self)
        optimize_action.triggered.connect(self.optimize_memory)
        tray_menu.addAction(optimize_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def update_metrics(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.text_label.setText(f"CPU: {cpu:.1f}%\nMEM: {mem:.1f}%")

    def start_wave(self):
        if not self.waving:
            self.waving = True
            self.wave_elapsed = 0
            self.wave_timer.start()

    def animate_wave(self):
        self.wave_elapsed += self.wave_timer.interval()
        progress = self.wave_elapsed / self.wave_duration
        if progress >= 1.0:
            self.wave_timer.stop()
            self.waving = False
            self.lightning_icon.move(self.lightning_icon.x(), 15)
            self.brain_icon.move(self.brain_icon.x(), 44)
            return
        offset = int(6 * math.sin(progress * 2 * math.pi))
        self.lightning_icon.move(self.lightning_icon.x(), 15 + offset)
        self.brain_icon.move(self.brain_icon.x(), 44 - offset)

    def animate_neon_border(self):
        self.neon_hue += self.neon_direction * 0.5
        if self.neon_hue >= 330:
            self.neon_hue = 330
            self.neon_direction = -1
        elif self.neon_hue <= 180:
            self.neon_hue = 180
            self.neon_direction = 1
        color = QColor.fromHsv(int(self.neon_hue), 255, 255).name()
        self.bg_label.setStyleSheet(f"""
            background-color: rgba(10, 10, 30, 180);
            border: 2px solid {color};
            border-radius: 12px;
        """)

    def show_close_button(self):
        self.close_button.show()
        self.hide_timer.start(3000)

    def close_widget(self, event=None):
        self.close()

    def optimize_memory(self):
        before = psutil.Process().memory_info().rss / (1024 * 1024)
        gc.collect()
        if sys.platform.startswith("win"):
            try:
                ctypes.windll.kernel32.SetProcessWorkingSetSize(
                    ctypes.windll.kernel32.GetCurrentProcess(), -1, -1
                )
            except Exception as e:
                self.text_label.setText("Memory optimization failed")
                return
            after = psutil.Process().memory_info().rss / (1024 * 1024)
            saved = before - after
            self.text_label.setText(f"✔ Optimized\n↓ {saved:.1f} MB")

            self.bg_label.setStyleSheet("""
                background-color: rgba(10, 30, 10, 220);
                border: 2px solid #00FF88;
                border-radius: 12px;
            """)
            QTimer.singleShot(1500, self.reset_border_style)
        else:
            self.text_label.setText("✔ GC run\n(Memory trim N/A)")

    def reset_border_style(self):
        color = QColor.fromHsv(int(self.neon_hue), 255, 255).name()
        self.bg_label.setStyleSheet(f"""
            background-color: rgba(10, 10, 30, 180);
            border: 2px solid {color};
            border-radius: 12px;
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.show_close_button()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def pulse_font_size(self):
        if self.pulse_growing:
            self.pulse_current += self.pulse_step
            if self.pulse_current >= self.pulse_max:
                self.pulse_current = self.pulse_max
                self.pulse_growing = False
        else:
            self.pulse_current -= self.pulse_step
            if self.pulse_current <= self.pulse_min:
                self.pulse_current = self.pulse_min
                self.pulse_growing = True

        font = self.optimize_button.font()
        font.setPointSizeF(self.pulse_current)
        self.optimize_button.setFont(font)

    def eventFilter(self, obj, event):
        if obj == self.optimize_button:
            if event.type() == event.Enter:
                self.pulse_timer.start()
            elif event.type() == event.Leave:
                self.pulse_timer.stop()
                font = self.optimize_button.font()
                font.setPointSize(self.pulse_min)
                self.optimize_button.setFont(font)
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Cyberpunk Monitor",
            "Running in background. Right-click the tray icon to exit.",
            QSystemTrayIcon.Information,
            3000
        )

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = CyberpunkMonitor()
    w.show()
    sys.exit(app.exec_())

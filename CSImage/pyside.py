import os
import sys
import time
import zlib

from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, \
                              QErrorMessage, \
                              QFileDialog, \
                              QGridLayout, \
                              QLabel, \
                              QMainWindow, \
                              QPlainTextEdit, \
                              QPushButton, \
                              QStackedWidget, \
                              QHBoxLayout, \
                              QVBoxLayout, \
                              QWidget
from search import ImageQueue, process
from threading import Thread

# TODO: Re-evaluate wheter threading would be worth it in Qt

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threadpool = QtCore.QThreadPool()
        self.resize(600, 350)
        self.carousel_widget = None
        self.results_widget = None
        self.select_widget = None
        self.image = QLabel()
        self.main_widget = QStackedWidget()
        self.setCentralWidget(self.main_widget)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.red)
        self.setPalette(p)
        self.status_bar = self.statusBar()
        self.status_msg = QLabel('')
        self.status_bar.addPermanentWidget(self.status_msg)
        self.setup_select_widget()
        self.match_widget, self.non_match_widget = self.setup_carousel_widget()
        self.setup_results_widget()
        self.main_widget.addWidget(self.select_widget)
        self.main_widget.addWidget(self.carousel_widget)
        self.main_widget.addWidget(self.results_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.main_widget)
        self.main_widget.setLayout(layout)
        self.setCentralWidget(self.main_widget)
        self.image_carousel = ImageQueue()

    def run(self, cwd):
        self.main_widget.setCurrentWidget(self.carousel_widget)
        processed, matches = 0, 0
        self.update_progress_status(processed=processed, matches=matches)
        for is_match, fpath, mem in process(cwd):
            if is_match:
                matches += 1
            processed += 1
            self.spin_the_carousel(is_match, fpath, mem)
            self.update_progress_status(processed=processed, matches=matches)
            QApplication.processEvents()
        self.show_results(cwd, processed, matches)

    def spin_the_carousel(self, is_match, fpath, mem):
        image = QImage()
        if image.loadFromData(zlib.decompress(mem)):
            widget_width = self.carousel_widget.width()
            if is_match:
                widget_width = widget_width // 2
            widget_height = self.carousel_widget.height()
            width, height = image.width(), image.height()
            if height > widget_height or width > widget_width:
                image = image.scaled(
                        QtCore.QSize(widget_width, widget_height),
                        aspectMode=QtCore.Qt.KeepAspectRatio
                    )
            if is_match:
                self.non_match_widget.setVisible(False)
                self.match_widget.setVisible(True)
                print(fpath)
            else:
                self.match_widget.setVisible(False)
                self.non_match_widget.setVisible(True)
            self.image.setPixmap(QPixmap.fromImage(image))

    def show_results(self, cwd, processed, matches):
        self.clear_progress_status()
        restart_btn = QPushButton('Restart')
        restart_btn.clicked.connect(self.restart)
        exit_btn = QPushButton('Exit')
        exit_btn.clicked.connect(self.exit)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        btn_layout.addStretch()
        btn_layout.addWidget(restart_btn)
        btn_layout.addWidget(exit_btn)
        btn_layout.addStretch()
        msg_layout = QVBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(25)
        msg_layout.setAlignment(QtCore.Qt.AlignCenter)
        msg_layout.addStretch()
        msg_layout.addWidget(QLabel(cwd))
        msg_layout.addWidget(QLabel(f'Processed {processed:,} images'))
        msg_layout.addWidget(QLabel(f'Found {matches:,} matches'))
        msg_layout.addStretch()
        layout = QVBoxLayout()
        layout.addLayout(msg_layout)
        layout.addLayout(btn_layout)
        self.results_widget.setLayout(layout)
        self.main_widget.setCurrentWidget(self.results_widget)

    def setup_select_widget(self):
        self.select_widget = QWidget()
        self.select_widget.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.green)
        self.select_widget.setPalette(p)
        label = QLabel('Choose a starting path below')
        select_btn = QPushButton('Select')
        select_btn.clicked.connect(self.get_cwd)
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(select_btn)
        self.select_widget.setLayout(layout)

    def setup_carousel_widget(self):
        match_text = QLabel('Match!')
        match_widget = QWidget()
        match_layout = QGridLayout()
        match_layout.addWidget(self.image, 0, 0)
        match_layout.addWidget(self.image, 0, 1)
        match_layout.addWidget(match_text, 1, 0, 1, 2)
        match_widget.setLayout(match_layout)

        non_match_widget = QWidget()
        non_match_layout = QVBoxLayout()
        non_match_layout.addWidget(self.image)
        non_match_widget.setLayout(non_match_layout)

        layout = QVBoxLayout()
        layout.addWidget(match_widget)
        layout.addWidget(non_match_widget)

        self.carousel_widget = QWidget()
        self.carousel_widget.setLayout(layout)
        return match_widget, non_match_widget

    def setup_results_widget(self):
        if self.results_widget is None:
            self.results_widget = QWidget()

    @QtCore.Slot()
    def get_cwd(self):
        cwd_dialog = QFileDialog(self)
        cwd_dialog.setFileMode(QFileDialog.Directory)
        if cwd_dialog.exec():
            if cwd := cwd_dialog.selectedFiles():
                cwd = cwd[0]
                if not os.path.isdir(cwd):
                    error_dialog = QErrorMessage(self)
                    error_dialog.showMessage('You must select a location to continue.')
                    # error_dialog.exe theses
                    return self.get_cwd()
                else:
                    '''
                    worker = CarouselThread(self.run, cwd)
                    worker.signals.finished.connect(self.show_results)
                    self.threadpool.start(worker)
                    '''
                    self.run(cwd)
                    return
        else:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage('You must select a location to continue.')
            # error_dialog.exe theses
            return self.get_cwd()

    @QtCore.Slot()
    def restart(self):
        self.clear_progress_status()
        self.main_widget.setCurrentWidget(self.select_widget)

    @QtCore.Slot()
    def exit(self):
        self.close()

    def clear_progress_status(self):
        self.status_msg.setText('')

    def update_progress_status(self, *, processed, matches):
        self.status_msg.setText(f'Processed: {processed} | Matches: {matches}')


class WorkerSignals(QtCore.QObject):

    finished = QtCore.Signal(tuple)


class CarouselThread(QtCore.QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        # TODO: Error handeling here and above
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            print(e)
        finally:
            return self.signals.finished.emit(result)



if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

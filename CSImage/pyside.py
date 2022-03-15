import os
import sys
import time
import zlib

from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QErrorMessage, \
                              QFileDialog, \
                              QGridLayout, \
                              QLabel, \
                              QMainWindow, \
                              QPushButton, \
                              QStackedWidget, \
                              QVBoxLayout, \
                              QWidget
from search import ImageQueue, process
from threading import Thread

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.status_msg = QLabel(f'Processed: {0} | Matches: {0}')
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
        carousel_thread = Thread(target=self.spin_the_carousel, daemon=True)
        carousel_thread.start()
        for is_match, fpath, mem in process(cwd):
            if is_match:
                matches += 1
            processed += 1
            self.image_carousel.put((is_match, fpath, mem))
            self.update_progress_status(processed=processed, matches=matches)
        self.image_carousel.close()
        self.image_carousel.join()
        carousel_thread.join()
        # self.show_results(cwd, processed, matches)
        print('here')

    def spin_the_carousel(self):
        for result in self.image_carousel:
            is_match, fpath, mem = result
            image = QImage()
            # TODO: Sizing, etc.
            if image.loadFromData(zlib.decompress(mem)):
                if is_match:
                    self.non_match_widget.setVisible(False)
                    self.match_widget.setVisible(True)
                    print(fpath)
                    # time.sleep(10)
                else:
                    self.match_widget.setVisible(False)
                    self.non_match_widget.setVisible(True)
                self.image.setPixmap(QPixmap.fromImage(image))

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
                    t = Thread(target=self.run, args=(cwd,))
                    t.start()
                    return
        else:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage('You must select a location to continue.')
            # error_dialog.exe theses
            return self.get_cwd()

    def update_progress_status(self, *, processed, matches):
        self.status_msg.setText(f'Processed: {processed} | Matches: {matches}')


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

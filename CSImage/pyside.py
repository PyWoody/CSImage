import os
import time
import zlib

from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, \
                              QErrorMessage, \
                              QFileDialog, \
                              QHBoxLayout, \
                              QGridLayout, \
                              QLabel, \
                              QMainWindow, \
                              QPushButton, \
                              QStackedWidget, \
                              QVBoxLayout, \
                              QWidget
from search import process


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.threadpool = QtCore.QThreadPool()
        self.resize(600, 350)
        self.carousel_widget = None
        self.results_widget = None
        self.select_widget = None
        self.match_image1, self.match_image2 = QLabel(), QLabel()
        self.non_match_image = QLabel()
        self.main_widget = QStackedWidget()
        self.setCentralWidget(self.main_widget)
        self.setAutoFillBackground(True)
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

    def run(self, cwd):
        """Initiates the processing of images and sets off the carousel

        args (required):
            cwd - The starting location where the images were processed
        """
        self.main_widget.setCurrentWidget(self.carousel_widget)
        processed, matches = 0, 0
        self.update_progress_status(processed=processed, matches=matches)
        for is_match, _, mem in process(cwd):
            if is_match:
                matches += 1
            processed += 1
            self.spin_the_carousel(is_match, mem)
            self.update_progress_status(processed=processed, matches=matches)
            QApplication.processEvents()
            if is_match:
                time.sleep(.25)
        self.show_results(cwd, processed, matches)

    def spin_the_carousel(self, is_match, mem):
        """Spins the carousel to add the necessary images.

        args (required)
            is_match - boolean for if the image is a match
            mem - A zlib compressed binary object for the image
        """
        border_size = 50
        image = QImage()
        if image.loadFromData(zlib.decompress(mem)):
            width, height = image.width(), image.height()
            widget_width = self.carousel_widget.width() - border_size
            widget_height = self.carousel_widget.height() - border_size
            if is_match:
                widget_width = widget_width // 2
                widget_height = widget_height // 2
            if height > widget_height or width > widget_width:
                image = image.scaled(
                        widget_width, widget_height,
                        aspectMode=QtCore.Qt.KeepAspectRatio
                    )
            pixmap = QPixmap.fromImage(image)
            if is_match:
                self.non_match_widget.setVisible(False)
                self.match_widget.setVisible(True)
                self.match_image1.setPixmap(pixmap)
                self.match_image2.setPixmap(pixmap)
            else:
                self.match_widget.setVisible(False)
                self.non_match_widget.setVisible(True)
                self.non_match_image.setPixmap(pixmap)

    def show_results(self, cwd, processed, matches):
        """Shows the results in the results widget.

        args (required):
            cwd - The starting location where the images were processed
            processed - Number of files processed
            matches - Number of matches
        """
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
        """Creates the select widget"""
        self.select_widget = QWidget()
        self.select_widget.setAutoFillBackground(True)
        label = QLabel('Choose a starting path below')
        select_btn = QPushButton('Select')
        select_btn.clicked.connect(self.get_cwd)
        layout = QGridLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setVerticalSpacing(25)
        layout.addWidget(label)
        layout.addWidget(select_btn, 1, 0, QtCore.Qt.AlignCenter)
        self.select_widget.setLayout(layout)

    def setup_carousel_widget(self):
        """Creates the carousel widget

        returns a tuple of layout widgets
        """
        match_widget = QWidget()
        match_layout = QGridLayout()
        match_layout.setAlignment(QtCore.Qt.AlignCenter)
        match_layout.addWidget(self.match_image1, 0, 0)
        match_layout.addWidget(self.match_image2, 0, 1)
        match_layout.addWidget(
            QLabel('Match!'), 1, 0, 1, 2, QtCore.Qt.AlignCenter
        )
        match_widget.setLayout(match_layout)

        non_match_widget = QWidget()
        non_match_layout = QVBoxLayout()
        non_match_layout.addWidget(self.non_match_image)
        non_match_widget.setLayout(non_match_layout)

        layout = QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(match_widget)
        layout.addWidget(non_match_widget)

        self.carousel_widget = QWidget()
        self.carousel_widget.setLayout(layout)
        return match_widget, non_match_widget

    def setup_results_widget(self):
        """Creates the results widget if needed""" 
        if self.results_widget is None:
            self.results_widget = QWidget()

    @QtCore.Slot()
    def get_cwd(self):
        """Initiates QFileDialog for getting starting directory

        If a valid directory is selected, `self.run` is started
        """
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
                    self.run(cwd)
                    return
        else:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage('You must select a location to continue.')
            # error_dialog.exe theses
            return self.get_cwd()

    @QtCore.Slot()
    def restart(self):
        """Returns the program to the default state"""
        self.clear_progress_status()
        self.main_widget.setCurrentWidget(self.select_widget)

    @QtCore.Slot()
    def exit(self):
        self.close()

    def clear_progress_status(self):
        self.status_msg.setText('')

    def update_progress_status(self, *, processed, matches):
        self.status_msg.setText(f'Processed: {processed} | Matches: {matches}')


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

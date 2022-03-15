import sys
import time
import zlib

from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGridLayout, \
                              QLabel, \
                              QMainWindow, \
                              QPushButton, \
                              QVBoxLayout, \
                              QWidget
from search import ImageQueue, process
from threading import Thread

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(600, 250)
        self.carousel_widget = None
        self.results_widget = None
        self.select_widget = None
        self.main_window = QMainWindow(self)
        self.processed, self.matches = 0, 0
        self.status_bar = self.statusBar()
        self.status_msg = QLabel(f'Processed: {0} | Matches: {0}')
        self.status_bar.addPermanentWidget(self.status_msg)
        self.setup_select_widget()
        self.setup_carousel_widget()
        self.setup_results_widget()
        # self.central_widget = self.select_widget
        self.central_widget = self.carousel_widget
        self.central_widget.show()
        '''
        self.central_widget.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
        )
        '''
        self.main_window.setCentralWidget(self.central_widget)
        self.main_window.show()
        self.image_carousel = ImageQueue()
        self.run(r'/home/sam/Projects')

    def run(self, cwd):
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

    def spin_the_carousel(self):
        for result in self.image_carousel:
            is_match, fpath, mem = result
            # image = QImage.loadFromData(QtCore.QByteArray(mem))
            image = QImage()
            if image.loadFromData(zlib.decompress(mem)):
                test = QLabel()
                test.setPixmap(QPixmap.fromImage(image))
                test.show()
                print(fpath)

    def setup_select_widget(self):
        label = QLabel('Choose a starting path below')
        select_btn = QPushButton('Select')
        select_btn.clicked.connect(self.get_cwd)
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(select_btn)
        # self.select_widget = QWidget()
        self.select_widget = QLabel('test')
        self.select_widget.setLayout(layout)

    def setup_carousel_widget(self):
        match_text = QLabel('Match!')
        # image1, image2 = '', ''
        image1, image2 = QLabel('image1'), QLabel('image2')
        layout = QGridLayout()
        layout.addWidget(image1, 0, 0)
        layout.addWidget(image2, 0, 1)
        layout.addWidget(match_text, 1, 0, 0, -1)
        self.carousel_widget = QWidget()
        self.carousel_widget.setLayout(layout)

    def setup_results_widget(self):
        if self.results_widget is None:
            self.results_widget = QWidget(self)

    @QtCore.Slot()
    def get_cwd(self):
        cwd_dialog = QFileDialog(self)
        cwd_dialog.setFileMode(QFileDialog.Directory)
        if cwd_dialog.exec():
            cwd = cwd_dialog.selectedFiles()
            if not os.path.isdir(cwd):
                error_dialog = QErrorMessage(self)
                error_dialog.showMessage('You must select a location to continue.')
                return self.get_cwd()
            else:
                self.run(cwd)
                return
        else:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage('You must select a location to continue.')
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

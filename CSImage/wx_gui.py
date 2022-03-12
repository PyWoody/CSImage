import os
import wx
import zlib

from io import BytesIO
from threading import Thread

from search import ImageQueue, process


class MainWindow(wx.Frame):

    def __init__(self, parent):
        super().__init__(parent, size=(600, 325))
        self.resized = False
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetBackgroundColour('red')
        self.Show(True)
        self.carousel_panel = None
        self.results_panel = None
        self.select_panel = None
        self.setup_select_panel()
        self.setup_carousel_panel()
        self.setup_results_panel()
        self.show_panel(self.select_panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.carousel_panel, 1, wx.EXPAND)
        sizer.Add(self.results_panel, 1, wx.EXPAND)
        sizer.Add(self.select_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.status_bar = self.CreateStatusBar()
        self.image_carousel = ImageQueue()

    def run(self, cwd):
        """Initiates the processing of images and sets off the carousel

        args (required):
            cwd - The starting location where the images were processed
        """
        processed, matches = 0, 0
        self.status_bar.SetFieldsCount(number=3, widths=(-1, 100, 100))
        self.status_bar.SetStatusText(f'Processed: {processed:,}', i=1)
        self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
        carousel_thread = Thread(target=self.spin_the_carousel, daemon=True)
        carousel_thread.start()
        for is_match, fpath, mem in process(cwd):
            if is_match:
                matches += 1
                self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
            processed += 1
            self.status_bar.SetStatusText(f'Processed: {processed:,}', i=1)
            self.image_carousel.put((is_match, fpath, mem))
            wx.Yield()
        self.image_carousel.close()
        self.image_carousel.join()
        carousel_thread.join()
        self.show_results(cwd, processed, matches)

    def spin_the_carousel(self):
        """Iterates over the self.image_carousel Queue to "spin" the carousel"""
        match_sizer, non_match_sizer  = self.setup_carousel_panel()
        match_bitmap1 = wx.StaticBitmap(self.carousel_panel)
        match_bitmap2 = wx.StaticBitmap(self.carousel_panel)
        non_match_bitmap = wx.StaticBitmap(self.carousel_panel)
        match_sizer.Add(match_bitmap1, 1, wx.EXPAND)
        match_sizer.Add(match_bitmap2, 1, wx.EXPAND)
        non_match_sizer.Add(non_match_bitmap, 1, wx.CENTER)
        self.Layout()
        width, height = self.GetSize()
        for result in self.image_carousel:
            is_match, fpath, mem = result
            if self.resized:
                width, height = self.GetSize()
                self.resized = False
            image = wx.Image()
            image.SetLoadFlags(0)
            if is_match:
                image.SetOption(wx.IMAGE_OPTION_MAX_WIDTH, (width // 2 ) - 5)
            else:
                image.SetOption(wx.IMAGE_OPTION_MAX_WIDTH, width)
            image.SetOption(wx.IMAGE_OPTION_MAX_HEIGHT, height)
            if image.LoadFile(BytesIO(zlib.decompress(mem))):
                converted_image = image.ConvertToBitmap()
                if is_match:
                    non_match_bitmap.Hide()
                    match_bitmap1.SetBitmap(converted_image)
                    match_bitmap1.Show()
                    match_bitmap2.SetBitmap(converted_image)
                    match_bitmap2.Show()
                else:
                    match_bitmap1.Hide()
                    match_bitmap2.Hide()
                    non_match_bitmap.SetBitmap(converted_image)
                    non_match_bitmap.Show()
                self.carousel_panel.Layout()

    def setup_carousel_panel(self):
        """Creates and promotes the self.carousel_panel if needed

        returns a tuple of bitmaps for matching, non-matching results
        """
        if self.carousel_panel is None:
            self.carousel_panel = wx.Panel(self)
        else:
            self.carousel_panel.DestroyChildren()
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        match_sizer = wx.GridSizer(rows=1, cols=2, vgap=0, hgap=5)
        non_match_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(match_sizer, 1, wx.CENTER)
        top_sizer.Add(non_match_sizer, 1, wx.CENTER)
        self.carousel_panel.SetSizer(top_sizer)
        self.carousel_panel.SetBackgroundColour('green')
        self.show_panel(self.carousel_panel)
        return match_sizer, non_match_sizer

    def setup_results_panel(self):
        """Creates and promotes the self.results_panel if needed"""
        if self.results_panel is None:
            self.results_panel = wx.Panel(self)
        self.show_panel(self.results_panel)

    def setup_select_panel(self):
        """Creates and promotes the self.select_panel if needed"""
        if self.select_panel is None:
            self.select_panel = wx.Panel(self)
            label = wx.StaticText(
                self.select_panel,
                label='Choose a starting path below'
            )
            start_btn = wx.Button(self.select_panel, label='Select')
            start_btn.Bind(wx.EVT_BUTTON, self.get_cwd, start_btn)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.AddStretchSpacer(1)
            sizer.Add(label, 0,  wx.ALIGN_CENTER, 20)
            sizer.AddSpacer(25)
            sizer.Add(start_btn, 0,  wx.ALIGN_CENTER, 20)
            sizer.AddStretchSpacer(1)
            self.select_panel.SetSizer(sizer)
            self.select_panel.SetBackgroundColour('yellow')
        self.show_panel(self.select_panel)

    def show_results(self, cwd, processed, matches):
        """Creates and shows the results panel.

        args (required):
            cwd - The starting location where the images were processed
            processed - Number of files processed
            matches - Nubmer of matches found
        """
        self.show_panel(self.results_panel)
        cwd_text = wx.StaticText(self.results_panel, label=cwd)
        processed_text = wx.StaticText(
            self.results_panel,
            label=f'Processed {processed:,} images'
        )
        matched_text = wx.StaticText(
            self.results_panel,
            label=f'Found {matches:,} matches'
        )
        restart_btn = wx.Button(self.results_panel, label='Restart?')
        restart_btn.Bind(wx.EVT_BUTTON, self.restart, restart_btn)
        exit_btn = wx.Button(self.results_panel, label='Exit')
        exit_btn.Bind(wx.EVT_BUTTON, self.close, exit_btn)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer(1)
        sizer.Add(cwd_text, 0, wx.ALIGN_CENTER)
        sizer.AddSpacer(25)
        sizer.Add(processed_text, 0, wx.ALIGN_CENTER)
        sizer.AddSpacer(25)
        sizer.Add(matched_text, 0, wx.ALIGN_CENTER)
        sizer.AddSpacer(25)
        sizer.Add(restart_btn, 0, wx.ALIGN_CENTER)
        sizer.AddSpacer(25)
        sizer.Add(exit_btn, 0, wx.ALIGN_CENTER)
        sizer.AddStretchSpacer(1)
        self.results_panel.SetSizer(sizer)
        self.results_panel.SetBackgroundColour('blue')
        self.Layout()

    def get_cwd(self, *event_args, **event_kwargs):
        """Initiates DirDialog for getting starting directory"""
        cwd_dialog = wx.DirDialog(
            None,
            'Choose staring location',
            '',  # Default path
            wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        if cwd_dialog.ShowModal() != wx.ID_OK:
            err_dialog = wx.MessageDialog(
                cwd_dialog,
                'You must select a location to continue.',
                caption='Error: Directory Not Selected',
                style=wx.ICON_ERROR | wx.OK | wx.CENTRE
            )
            err_dialog.ShowModal()
            return
        cwd = cwd_dialog.GetPath()
        if not os.path.isdir(cwd):
            err_dialog = wx.MessageDialog(
                cwd_dialog,
                f'{cwd} does not exist',
                style=wx.ICON_ERROR | wx.OK | wx.CENTRE
            )
            err_dialog.ShowModal()
        else:
            self.run(cwd)
            return

    def restart(self, *event_args, **event_kwargs):
        """Re-initializes the program to its default, starting position"""
        for idx in range(self.status_bar.GetFieldsCount()):
            self.status_bar.SetStatusText('', i=idx)
        self.results_panel.DestroyChildren()
        self.carousel_panel.DestroyChildren()
        self.setup_carousel_panel()
        self.show_panel(self.select_panel)


    def show_panel(self, panel):
        """Shows the specified panel and hides all other wx.Panels"""
        for child in self.GetChildren():
            if isinstance(child, wx.Panel) and child is not panel:
                child.Hide()
        panel.Show()
        self.Layout()

    def on_resize(self, *event_args, **event_kwargs):
        self.resized = True

    def close(self, *args, **kwargs):
        self.Close()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()

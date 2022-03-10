import os
import wx

from threading import Thread

from search import ImageQueue, process


class MainWindow(wx.Frame):

    def __init__(self, parent):
        super().__init__(parent, size=(600, 325))
        self.SetBackgroundColour('red')
        self.Show(True)
        self.carousel_panel = None
        self.select_panel = None
        self.setup_select_panel()
        self.setup_carousel_panel()
        self.carousel_panel.Hide()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.carousel_panel, 1, wx.EXPAND)
        sizer.Add(self.select_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.status_bar = self.CreateStatusBar()
        self.status_bar.PushStatusText('Select a starting point to begin...')
        self.image_carousel = ImageQueue()

    def run(self, cwd):
        # 0: Processing...{fname}
        # 1: Total Processed
        # 2: Matches found
        self.select_panel.Hide()
        wx.Yield()
        processed, matches = 0, 0
        self.status_bar.SetFieldsCount(number=3, widths=(-1, 100, 100))  # check min width
        self.status_bar.SetStatusText(f'Processing {cwd}...', i=0)
        self.status_bar.SetStatusText(f'Total: {processed:,}', i=1)
        self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
        carousel_thread = Thread(target=self.spin_the_carousel, daemon=True)
        carousel_thread.start()
        for unique, fpath in process(cwd):
            processed += 1
            if unique:
                matches += 1
                self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
            self.status_bar.SetStatusText(f'Processing {fpath}...', i=0)
            self.status_bar.SetStatusText(f'Total: {processed:,}', i=1)
            wx.Yield()
            self.image_carousel.put((unique, fpath))
        self.image_carousel.close()
        self.image_carousel.join()
        self.show_results(cwd, processed, matches)
        print('done')

    def spin_the_carousel(self):
        static_bitmap = self.setup_carousel_panel()
        for result in self.image_carousel:
            unique, fpath = result
            image = wx.Image()
            if image.CanRead(fpath):
                image.SetLoadFlags(0)
                image.LoadFile(open(fpath, 'rb'))
                if image.IsOk():
                    print(fpath)
                    static_bitmap.SetBitmap(image.ConvertToBitmap())
                    self.Layout()
                    wx.Yield()
                    continue
                    if unique:
                        pass
                    else:
                        pass

    def setup_carousel_panel(self):
        if self.carousel_panel is None:
            # self.carousel_panel.Destroy()
            self.carousel_panel = wx.Panel(self)
        static_bitmap = wx.StaticBitmap(self.carousel_panel)
        static_bitmap.SetScaleMode(wx.StaticBitmap.ScaleMode.Scale_AspectFit)
        sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer.Add(static_bitmap, 1, wx.EXPAND | wx.CENTER)
        sizer.Add(static_bitmap, 1, wx.CENTER)
        self.carousel_panel.SetSizer(sizer)
        self.carousel_panel.SetBackgroundColour('green')
        self.carousel_panel.Show()
        self.Layout()
        return static_bitmap

    def setup_select_panel(self):
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
        self.select_panel.Show()

    def show_results(self, cwd, processed, matches):
        pass

    def get_cwd(self, *event_args, **event_kwargs):
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


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()

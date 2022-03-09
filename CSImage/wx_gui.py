import os, wx

from search import process

class MainWindow(wx.Frame):

    def __init__(self, parent):
        super().__init__(parent, size=(600, 325))
        self.Show(True)
        self.select_panel = None
        self.process_panel = None
        self.setup_select_panel()
        self.status_bar = self.CreateStatusBar()
        self.status_bar.PushStatusText('Select a starting point to begin...')

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
            sizer.SetSizeHints(self.select_panel)
            self.select_panel.SetSizer(sizer)
        self.select_panel.Show()

    def _setup_select_panel(self):
        if self.select_panel is None:
            self.select_panel = wx.Panel(self)
            label = wx.StaticText(
                self.select_panel,
                label='Choose a starting path below'
            )
            start_btn = wx.Button(self, label='Select')
            self.Bind(wx.EVT_BUTTON, self.get_cwd, start_btn)
            # sizer is broken when on subsequent runs
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.AddStretchSpacer(1)
            sizer.Add(label, 0,  wx.ALIGN_CENTER, 20)
            sizer.AddSpacer(25)
            sizer.Add(start_btn, 0,  wx.ALIGN_CENTER, 20)
            sizer.AddStretchSpacer(1)
            sizer.SetSizeHints(self.select_panel)
            self.SetSizer(sizer)
        self.select_panel.Show()

    def teardown_select_panel(self):
        self.select_panel.Destroy()
        self.select_panel = None

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

    def run(self, cwd):
        # 0: Processing...{fname}
        # 1: Total Processed
        # 2: Matches found
        self.teardown_select_panel()
        if self.process_panel is None:
            self.process_panel = wx.Panel(self, wx.ID_ANY)
        processed, matches, prev_processed, prev_matches = 0, 0, 0, 0
        self.status_bar.SetFieldsCount(number=3, widths=(-1, 100, 100))  # check min width
        # use self.status_bar.SetStatusText(text, i=int)
        self.status_bar.SetStatusText(f'Processing {cwd}...', i=0)
        self.status_bar.SetStatusText(f'Total: {processed:,}', i=1)
        self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
        for unique, fpath in process(cwd):
            print(unique, fpath)


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()

import os, wx

from search import process

class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(300, 175))
        self.Show(True)

        # Status bar
        self.status_bar = self.CreateStatusBar()
        self.status_bar.PushStatusText('Select a starting point to begin...')

        cwd = self.get_cwd()
        self.run(cwd)

    def get_cwd(self):
        cwd_dialog = wx.DirDialog(
            None,
            'Choose staring location',
            '',  # Default path
            wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        if cwd_dialog.ShowModal() != wx.ID_OK:
            err_dialog = wx.MessageDialog(
                cwd_dialog,
                caption=f'You must select a location to continue.',
                style=wx.ERROR | wx.OK | wx.CENTRE
            )
            err_dialog.ShowModal()
            del cwd_dialog
            return self.get_cwd()
        cwd = cwd_dialog.GetPath()
        if not os.path.isdir(cwd):
            err_dialog = wx.MessageDialog(
                cwd_dialog,
                caption=f'{cwd} does not exist',
                style=wx.ERROR | wx.OK | wx.CENTRE
            )
            err_dialog.ShowModal()
        else:
            return cwd

    def run(self, cwd):
        # 0: Processing...{fname}
        # 1: Total Processed
        # 2: Matches found
        processed, matches, prev_processed, prev_matches = 0, 0, 0, 0
        self.status_bar.SetFieldsCount(number=3, widths=(-1, 100, 100))
        # use self.status_bar.SetStatusText(text, i=int)
        self.status_bar.SetStatusText(f'Processing {cwd}...', i=0)
        self.status_bar.SetStatusText(f'Total: {processed:,}', i=1)
        self.status_bar.SetStatusText(f'Matches: {matches:,}', i=2)
        pass


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None, 'CSImage Searver - wxPython')
    app.MainLoop()

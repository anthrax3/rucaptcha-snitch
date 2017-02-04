"""
GUI HELPER TOOL TO MANUALLY REVIEW AND SNITCH ON INCORRECT RUCAPTCHA SOLVES

!!  CAPTCHA IDs EXPIRE AFTER 15 MIN, IF THAT IS THE CASE, YOU'll GET
!!  'ERROR_WRONG_CAPTCHA_ID'

Overview:
    1. spawn gui with captcha image and result of solve
    2. two buttons - correct / incorrect
    3. incorrect? add to snitch list : add to correct list
    4. archive correct
    5. for entry in snitch list, report incorrect
    6. report successful? archive : print failed response to console

image name should be <captchaX_Y> where X - captcha id, Y - solved string
ie 'captcha2508000710_nmcfx.png'

Settings:
    :apikey: for rucaptcha first line in file './key.txt'
    :captcha_dir: see (class) SnitchRunner.captcha_dir
    :archive_dir: see (class) SnitchRunner.archive_dir


TODO: run in infinite loop continuosly polling directory for new captchas
"""
import os
import requests
import Tkinter as Tk
import tkFont
from PIL import Image, ImageTk
import time


class SnitchGui(object):
    """
    spawn a window with captcha image for quick self entry
    :param captcha_file: <path to image>
    """

    def __init__(self, captcha_file):
        self.captcha_id = captcha_file.split('_')[0].split('a')[-1]
        self.captcha_solved = captcha_file.split('_')[1].split('.')[0]
        self.master = Tk.Tk()
        self.canvas = Tk.Canvas(self.master, width=220, height=50)
        self.label = Tk.Label(self.master, text=self.captcha_solved)
        self.button_correct = Tk.Button(self.master, text='Correct',
                                        command=self.correct)
        self.button_incorrect = Tk.Button(self.master, text='Incorrect',
                                          command=self.incorrect)
        self.captcha = ImageTk.PhotoImage(Image.open(captcha_file))
        self.font = tkFont.Font(size=16)
        self.id_incorrect = ''
        self.id_correct = ''
        self.uinit()

    def run(self):
        self.master.lift()
        self.master.focus_force()
        self.master.mainloop()

    def uinit(self):
        self.center()
        self.master.minsize(width=220, height=200)
        self.master.maxsize(width=220, height=400)
        self.master.title('Rucaptcha Snitch')

        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.captcha, anchor='nw')
        self.label.pack(fill='both', expand='yes')
        self.label['font'] = self.font
        self.button_correct.pack(fill='both', expand='yes')
        self.button_correct['font'] = self.font
        self.button_incorrect.pack(fill='both', expand='yes')
        self.button_incorrect['font'] = self.font

    def center(self):
        """ center master on screen """
        self.master.update_idletasks()
        scr_w = self.master.winfo_screenwidth()
        scr_h = self.master.winfo_screenheight()
        win_w, win_h = [int(x) for x in
                        self.master.geometry().split('+')[0].split('x')]

        cord_x = scr_w / 2 - win_w / 2
        cord_y = scr_h / 2 - win_h / 2
        pos = '%dx%d+%d+%d' % (win_w, win_h, cord_x, cord_y)
        self.master.geometry(pos)

    def correct(self, *args):
        self.id_correct = self.captcha_id
        self.master.destroy()

    def incorrect(self, *args):
        self.id_incorrect = self.captcha_id
        self.master.destroy()


class SnitchRunner(object):
    def __init__(self, apikey):
        self.snitch_list = []
        self.correct_list = []
        self.captcha_dir = './'
        self.archive_dir = '../archive/'
        self.key = apikey

    def snitch(self, capt_id):
        """ report failed captcha """
        url = 'http://rucaptcha.com/res.php'
        h = {'User-Agent': 'snitch'}
        d = {'key': self.key, 'action': 'reportbad', 'id': capt_id}
        res = requests.get(url, headers=h, params=d)
        return res

    def run(self):
        """
        main method
        """

        for filename in self.list_files():
            sngui = SnitchGui(filename)
            sngui.run()

            if sngui.id_incorrect:
                self.snitch_list.append([filename, sngui.id_incorrect])
            elif sngui.id_correct:
                self.correct_list.append([filename, sngui.id_correct])
            else:
                raise Exception('no correct or incorrect')

        for filename, id_correct in self.correct_list:
            self.archive(filename)

        for filename, id_snitch in self.snitch_list:
            res = self.snitch(id_snitch)
            if res.content.startswith('OK_REPORT_RECORDED'):
                print res.content + ' id: %s' % id_snitch
                self.archive(filename)
                time.sleep(1)
            else:
                print res.content + ' id: %s' % id_snitch

    def list_files(self):
        """ return list of captcha filenames """
        l = []
        for filename in os.listdir(self.captcha_dir):
            if filename.startswith('captcha'):
                l.append(filename)
        return l

    def archive(self, filename):
        """ move file to archive dir """
        os.rename(self.captcha_dir + filename, self.archive_dir + filename)


if __name__ == '__main__':
    with open('key.txt') as infile:
        key = infile.readline().strip()
    snitch = SnitchRunner(apikey=key)
    snitch.run()

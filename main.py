import os
import shutil
from pathlib import Path
import configparser
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import END, INSERT, VERTICAL, HORIZONTAL, N, S, E, W, filedialog
import ttkbootstrap as ttk
import time
import datetime
import queue
import logging
import signal
import time
import threading
import ctypes

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

CONFIG_SUFFIX = 'Hot Folder Suffix'
CONFIG_OUTPUT = 'Hot Folder Output'
CONFIG_LOCATION = 'Hot Folders Location'

PROGRAM_LOCATION = os.getcwd()

folder_options = []

app = None
t1 = None

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E)) # type: ignore
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=True)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s', '%m/%d/%Y %H:%M:%S')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class ThirdUi:

    def __init__(self, frame):
        self.frame = frame
        
        self.folder_name = tk.StringVar()
        self.folder_location = tk.StringVar()
        self.suffix = tk.StringVar()
        self.folder_output_location = tk.StringVar()
        self.folder_name_selected = tk.StringVar()
        
        tk.Label(self.frame, text= 'Folder Name').place(x = 240, y = 10)
        tk.Entry(self.frame, textvariable= self.folder_name, width = 35, name = 'folder name entry').pack(pady= 10)
        tk.Label(self.frame, text = 'Folder Location').place(x = 230, y = 50)
        self.folder_location_entry = tk.Entry(self.frame, textvariable= self.folder_location, width = 35, name = 'folder input entry')
        self.folder_location_entry.pack(pady= 10)
        ttk.Button(self.frame, text= 'Browse', command= lambda: self.browse_folder('input'), bootstyle = 'outline').place(x = 575, y = 45)
        tk.Label(self.frame, text= 'Folder Suffix').place(x = 240, y = 90)
        self.suffix_entry = tk.Entry(self.frame, textvariable= self.suffix, width = 35, name = 'folder suffix entry')
        self.suffix_entry.pack(pady= 10)
        tk.Label(self.frame, text= 'Output Folde Location').place(x = 200, y = 130)
        self.folder_output_location_entry = tk.Entry(self.frame, textvariable= self.folder_output_location, width= 35, name = 'folder output entry')
        self.folder_output_location_entry.pack(pady = 10)
        ttk.Button(self.frame, text = 'Browse', command= lambda: self.browse_folder('output'), bootstyle = 'outline').place(x = 575, y = 130)
        ttk.Button(self.frame, text= 'Create Folder', command= self.create_folder, bootstyle = 'outline').pack(pady = 10)
        self.folder_name_selected.set("Folder Name")
        ttk.OptionMenu(self.frame, variable=self.folder_name_selected, *folder_options).place(x = 100, y = 10)
        
        
    def browse_folder(self, entry_name):
        if 'input' in entry_name:
            self.folder_location = filedialog.askdirectory(title= 'Select a Folder')
            self.folder_location_entry.delete(0, END)
            self.folder_location_entry.insert(0, self.folder_location)
            logger.log(logging.INFO, msg= f'Input Folder Location = {self.folder_location}')
        elif 'output' in entry_name:
            self.folder_output_location = filedialog.askdirectory(title= 'Select a Folder')
            self.folder_output_location_entry.delete(0, END)
            self.folder_output_location_entry.insert(0, self.folder_output_location)
            logger.log(logging.INFO, msg= f'Output Folder Location = {self.folder_output_location}')
    
    def create_folder(self):
        folder_name = self.folder_name.get()
        folder_input = self.folder_location
        folder_suffix = self.suffix.get()
        folder_output = self.folder_output_location
        
        create_new_hot_folder(folder_name= folder_name, folder_input= folder_input, folder_suffix= folder_suffix, folder_output= folder_output)

class App:

    def __init__(self, root):
        self.root = root
        if os.path.exists(f'{PROGRAM_LOCATION}/myapp.conf'):
            with open(f'{PROGRAM_LOCATION}/myapp.conf', 'r') as file:
                postion = file.read()
            file.close()
        self.root.geometry(postion)
        root.resizable(False, False)
        root.title('Main GUI')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # Create the panes and frames
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)
        console_frame = ttk.Labelframe(vertical_pane, text="Console")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        vertical_pane.add(console_frame, weight=1)
        third_frame = ttk.Labelframe(horizontal_pane, text="Create new Hot Folder")
        third_frame.columnconfigure(0, weight=1)
        third_frame.rowconfigure(2, weight=1)
        horizontal_pane.add(third_frame, weight=1)
        # Initialize all frames
        self.third = ThirdUi(third_frame)
        self.console = ConsoleUi(console_frame)
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        with open(f"{PROGRAM_LOCATION}/myapp.conf", "w") as conf:
            conf.write(self.root.winfo_geometry()) 
        conf.close()
        t1.raise_exception()
        t1.join()
        self.root.destroy()


def adding_to_file_name(options, number_of_files):
    hot_folder_location = config.get(CONFIG_LOCATION, options)
    hp_hot_folder_location = config.get(CONFIG_OUTPUT, options)
    name_suffix = config.get(CONFIG_SUFFIX, options)

    i = 1

    while i <= number_of_files:
        for file in os.listdir(hot_folder_location):
            p = Path(file)
            new_file_name = "{0}{2}{1}".format(p.stem, p.suffix, name_suffix)
            if p.suffix == '.txt' or p.suffix == '.pdf':
                shutil.move(f'{hot_folder_location}/{file}', f'{hp_hot_folder_location}/{new_file_name}')
                logger_name = f'{file} change to {new_file_name}'
                logger.log(logging.INFO, msg= logger_name)
                i += 1
                time.sleep(2)
            else:
                i += 1
                logger_msg = f'There\'s a non PDF file in {hot_folder_location}. Please remove it.'
                logger.log(logging.INFO, msg = logger_msg)
        

def create_new_hot_folder(folder_name, folder_input, folder_suffix, folder_output):
    global app, folder_options
    new_folder = str(folder_name)
    new_folder_location = str(folder_input)
    new_suffix = str(folder_suffix)
    new_output_location = str(folder_output)
    
    os.mkdir(f'{new_folder_location}/{new_folder}')
    logger.log(logging.INFO, msg= 'Creating Folder......')
    logger.log(logging.INFO, msg = 'Folder has been created.....')
    config[CONFIG_LOCATION][new_folder] = f'{new_folder_location}/{new_folder}'
    config[CONFIG_SUFFIX][new_folder] = f'_{new_suffix}'
    config[CONFIG_OUTPUT][new_folder] = new_output_location
    with open('config.ini', 'w') as configFile:
        config.write(configFile)
    
    logger.log(logging.INFO, msg= 'Saving folder settings.....')
    logger.log(logging.INFO, msg= 'Folder setting has been saved.....')
    
    app.third.frame.children['folder name entry'].delete(0, END)
    app.third.frame.children['folder input entry'].delete(0, END)
    app.third.frame.children['folder suffix entry'].delete(0, END)
    app.third.frame.children['folder output entry'].delete(0, END)
    config.read('config.ini')
    folder_options.append(new_folder)

    
    
class main_thread_with_exception(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
             
    def run(self):
 
        # target function of the thread class
        try:
            while True:
                main_run()
        finally:
            logger.log(logging.INFO, 'Stopping App...')
          
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


class folder_creating_thread_with_exception(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
             
    def run(self):
 
        # target function of the thread class
        try:
            while True:
                create_new_hot_folder()
        finally:
            logger.log(logging.INFO, 'Stopping App...')
          
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

def main_run():
    get_time = lambda f: os.stat(f).st_ctime
    
    prev_time = get_time('config.ini')

    while True:
        time.sleep(10)
        
        t = get_time('config.ini')
        
        if t != prev_time:
            config.read('config.ini')
            prev_time = get_time('config.ini')
            
        configOptions = config.options(CONFIG_LOCATION)
            
        if len(configOptions) == 0:
            message = 'Please create the first Hot Folder.'
            logger.log(logging.INFO, msg= message)
            while len(configOptions) == 0:
                time.sleep(2)
                configOptions = config.options(CONFIG_LOCATION)
        
        for options in config.options(CONFIG_LOCATION):
            try:
                dir_len = len(os.listdir(config.get(CONFIG_LOCATION, options)))
                if dir_len != 0:
                    adding_to_file_name(options, dir_len)
            except:
                message = f'Could not find folder: {config.get(CONFIG_LOCATION, options)}. Please go to the config.ini file and correct the folder location'
                logger.log(logging.INFO, msg = message)




def main():
    global app, t1, folder_options
    logging.basicConfig(level=logging.DEBUG)

    for options in config.options(CONFIG_LOCATION):
        folder_options.append(options)

    root = tk.Tk()
    app = App(root)

    logger.log(logging.INFO, msg = 'Starting App')
    t1 = main_thread_with_exception('run')
    t1.start()

    app.root.mainloop()

if __name__ == "__main__":
    
    main()
    
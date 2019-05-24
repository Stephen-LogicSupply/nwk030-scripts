import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import serial
import time
import logging

logging.basicConfig(filename='FTP_TEST.log', level=logging.DEBUG)
_logger = logging.getLogger("FTP_TEST")

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

_logger.addHandler(ch)


def find_port():
    """
    Finds if the inserted modem is installed, and gets its port

    ::returns:: modem, system

    ::param modem:: The COM port the modem is attached to
    ::type modem:: string variable

    ::param system::  The name of the detected modem type
    ::type system:: string variable
    """
    coms = []
    open_ports = []

    # native_com_list = list_ports.comports(True)

    for port in range(1, 256):
        com_check = "COM" + str(port)
        try:
            s = serial.Serial(com_check)
            s.close()
            open_ports.append(com_check)
            _logger.debug("%s port is populated", com_check)
        except (OSError, serial.SerialException):
            _logger.debug("%s port is not populated", com_check)
        pass

    modem = list(set(open_ports) - set(coms))

    if len(modem) > 1:
        for test_port in modem:
            test_ser = open_serial_connection(test_port)
            test_ser.write(b"ATE1\r\n")
            if str(test_ser.readline()) == str(b'ATE1\r\r\n'):
                modem[0] = test_port
                _logger.info("Port found: %s", str(test_port))

    return modem[0]


def open_serial_connection(port):
    """
    Opens the serial connection and establishes parameters

    ::param port:: COM port for the modem
    ::type port:: String variable

    ::returns:: ser

    ::param ser:: Com Object for 4G Modem
    ::type ser:: Open serial.Serial com object
    """
    _logger.info("Searching for modem")
    ser = serial.Serial(port)

    ser.close()
    ser.open()
    ser.baudrate = 115200
    ser.bytesize = 8
    ser.Parity = 'N'
    ser.stopbits = 1
    ser.timeout = 15

    return ser


class ATFTPGUI:
    def __init__(self, master):
        """
        Initializes gui and connect to the modem
        """
        com = find_port()
        _logger.debug("Selected port is %s", com)
        self.ser = serial.Serial(com, baudrate=9600, timeout=.1, rtscts=0)
        self.master = master
        master.title("FTP over LTE-cat: M1")
        master.geometry('500x200')

        self.IP_lbl = tk.Label(master, text="URL:")
        self.IP_lbl.grid(column=1, row=0)

        self.IP_entry = tk.Entry(master, width=20)
        self.IP_entry.grid(column=2, row=0)

        self.port_lbl = tk.Label(master, text="PORT #:")
        self.port_lbl.grid(column=1, row=1)

        self.port_entry = tk.Entry(master, width=20)
        self.port_entry.grid(column=2, row=1)

        self.username_lbl = tk.Label(master, text="Username:")
        self.username_lbl.grid(column=1, row=2)

        self.username_entry = tk.Entry(master, width=20)
        self.username_entry.grid(column=2, row=2)

        self.pass_lbl = tk.Label(master, text="Password:")
        self.pass_lbl.grid(column=1, row=3)

        self.pass_entry = tk.Entry(master, width=20, show="*")
        self.pass_entry.grid(column=2, row=3)

        self.connect_button = tk.Button(master, text="Connect", command=self.connect)
        self.connect_button.grid(column=2, row=4)

        self.file_lbl = tk.Label(master, text="")
        self.file_lbl.grid(column=2, row=6)

        self.notification_lbl = tk.Label(master, text="")
        self.notification_lbl.grid(column=2, row=6)

        self.browse_button = tk.Button(master, text="Browse", state=tk.DISABLED, command=self.browse)
        self.browse_button.grid(column=2, row=5)

        self.upload_button = tk.Button(master, text="Upload", state=tk.DISABLED, command=self.upload)
        self.upload_button.grid(column=3, row=5)

        self.close_button = tk.Button(master, text="Close", command=self.close)
        self.close_button.grid(column=2, row=7)

        self.progress = ttk.Progressbar(master, orient="horizontal", length=150, mode="determinate")
        self.progress.grid(column=4, row=1)

    def connect(self):
        """
        Connects to an FTP server
        """
        url = self.IP_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()
        password = self.pass_entry.get()
        self.establish(url, port, username, password)

        self.browse_button.configure(state=tk.NORMAL)
        self.connect_button.configure(state=tk.DISABLED)

    def browse(self):
        """
        Opens a file for upload
        """
        filename = askopenfilename()
        self.file_lbl.config(text=filename)
        self.upload_button.configure(state=tk.NORMAL)

    def establish(self, url, port, username, password):
        """
        Opens connection to an FTP server

        ::param url:: User defined url for the FTP server
        ::type url:: String variable

        ::param port:: User defined port that the FTP server is set to
        ::type port:: Integer variable

        ::param username:: User defined name for login to FTP
        ::type username:: String variable

        ::param password:: User defined password for the entered username
        ::type password:: String variable
        """

        self.progress["value"] = 0
        self.progress["maximum"] = 6
        count = 0
        cmd = "AT+cgdcont?\r\n"
        _logger.info(cmd)
        self.ser.write(cmd.encode())
        root.update()
        response = self.ser.read(self.ser.inWaiting())
        _logger.info(response)
        if "\"0.0.0.0 " in response.decode():
            _logger.info("NO CELLULAR CONNECTION")
            self.ser.write(b'at+CFUN=15\r\n')
            time.sleep(2)
            tk.sys.exit()

        count += 1
        cmd = "AT+USOCR=6\r\n"
        self.commandCall(cmd, count)

        # Set FTP address
        count += 1
        cmd = "AT+UFTP=1,\"" + url + "\"\r\n"
        self.commandCall(cmd, count)

        # set username
        count += 1
        cmd = "AT+UFTP=2,\"" + username + "\"\r\n"
        self.commandCall(cmd, count)

        # set password
        count += 1
        cmd = "AT+UFTP=3,\"" + password + "\"\r\n"
        self.commandCall(cmd, count)

        # set to passive mode
        count += 1
        cmd = "AT+UFTP=6,1\r\n"
        self.commandCall(cmd, count)

        # set port number
        count += 1
        cmd = "AT+UFTP=7," + port + "\r\n"
        self.commandCall(cmd, count)
        self.progress["value"] = 0

    def commandCall(self, cmd, count):
        """
        Parse the various AT commands used to interact with the modem

        ::param cmd:: User defined url for the FTP server
        ::type cmd:: String variable

        ::param count:: User defined port that the FTP server is set to
        ::type count:: Integer variable
        """
        self.progress["value"] = count
        root.update_idletasks()
        _logger.info(cmd)
        self.ser.write(cmd.encode())
        time.sleep(3)
        _logger.info(self.ser.read(self.ser.inWaiting()))

    def upload(self):
        """
        Upload a file to the connected FTP server
        """
        count = 1
        self.progress["maximum"] = 43
        # login
        cmd = "AT+UFTPC=1\r\n"
        self.commandCall(cmd, count)

        # get the size and contents of the file
        filename = self.file_lbl.cget("text")
        f = open(filename)
        ftext = f.read()
        f.close()

        # set directory to 'ftp' on the server
        count += 1
        cmd = "at+UFTPC=8,\"ftp\"\r\n"
        self.commandCall(cmd, count)

        # Send a file to the FTP server using the direct link mode
        # this takes a file name and the contents of a file, it doesn't actually upload the file itself
        count += 1
        cmd = "AT+UFTPC=7,\"test2.txt\"\r\n"
        self.commandCall(cmd, count)

        _logger.info("UPLOADING THE FILE")
        self.ser.write(ftext.encode())
        time.sleep(5)

        # end direct link mode
        cmd = "+++"
        _logger.info(cmd)
        self.ser.write(cmd.encode())
        for tick in range(0, 40):
            time.sleep(1)
            count += 1
            self.progress["value"] = count
            root.update_idletasks()

        _logger.info(self.ser.read(self.ser.inWaiting()))
        self.progress["value"] = 0
        root.update_idletasks()

    def close(self):
        """
        Closes the program and resets the modem
        """
        self.ser.write(b'at+CFUN=15\r\n')
        _logger.info("RESTARTING THE MODEM")
        time.sleep(1)
        tk.sys.exit()


root = tk.Tk()
gui = ATFTPGUI(root)
root.mainloop()

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import shutil
import threading
import time
import importlib
import sys

# Define the required system packages
required_system_packages = [
    'mtools',  # Required for mcopy
    'dosfstools',  # Required for mkfs.vfat
    'lsblk'  # Required for lsblk
]

# Define the required Python packages
required_python_packages = [
    'tkinter',  # Included in Python standard library but might need explicit installation
    'subprocess',  # Included in Python standard library
    'os',  # Included in Python standard library
    'shutil',  # Included in Python standard library
    'threading',  # Included in Python standard library
    'time',  # Included in Python standard library
    'importlib'  # Included in Python standard library
]

def check_required_packages():
    """Check if the required system packages are installed."""
    missing_packages = []
    for pkg in required_system_packages:
        try:
            subprocess.check_call(['dpkg', '-s', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing_packages.append(pkg)
    return missing_packages

def install_required_packages(packages):
    """Install the missing system packages."""
    if packages:
        try:
            subprocess.run(['sudo', 'apt', 'install', '-y'] + packages, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror('Error', f'Failed to install required packages: {e}')

def check_python_packages():
    """Check if the required Python packages are installed."""
    missing_packages = []
    for pkg in required_python_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing_packages.append(pkg)
    return missing_packages

def install_python_packages(packages):
    """Install the missing Python packages."""
    if packages:
        try:
            subprocess.run(['pip', 'install'] + packages, check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror('Error', f'Failed to install Python packages: {e}')

def ensure_sudo():
    """Ensure the script is run with sudo."""
    if os.geteuid() != 0:
        messagebox.showerror('Permission Error',
                             'This script requires superuser privileges. Please run with sudo.')
        sys.exit()

def get_removable_drives():
    """Get a list of removable /dev/sdX drives, excluding /dev/sda."""
    try:
        output = subprocess.check_output(['lsblk', '-o', 'NAME,TYPE', '-n', '-l'], text=True)
        drives = [f'/dev/{line.split()[0]}' for line in output.splitlines() 
                  if line.startswith('sd') and line.split()[0] != 'sda']
        return drives
    except subprocess.CalledProcessError as e:
        messagebox.showerror('Error', f'Failed to get drives.\n{e}')
        return []

def get_all_drives():
    """Get a list of all /dev/sdX drives."""
    try:
        output = subprocess.check_output(['lsblk', '-o', 'NAME,TYPE', '-n', '-l'], text=True)
        all_drives = [f'/dev/{line.split()[0]}' for line in output.splitlines() if line.startswith('sd')]
        return all_drives
    except subprocess.CalledProcessError as e:
        messagebox.showerror('Error', f'Failed to get drives.\n{e}')
        return []

def get_partitions(drive):
    """Get a list of partitions for a given drive."""
    try:
        output = subprocess.check_output(['lsblk', '-o', 'NAME,MOUNTPOINT', '-n', '-l'], text=True)
        partitions = [line.split()[0] for line in output.splitlines() if line.startswith(drive.split('/')[-1])]
        return partitions
    except subprocess.CalledProcessError as e:
        messagebox.showerror('Error', f'Failed to get partitions.\n{e}')
        return []

def format_drive(drive, fs_type):
    """Format the selected drive with the chosen filesystem."""
    try:
        if fs_type == 'FAT16':
            subprocess.run(['sudo', 'mkfs.vfat', '-F', '16', drive], check=True)
        elif fs_type == 'FAT32':
            subprocess.run(['sudo', 'mkfs.vfat', '-F', '32', drive], check=True)
        else:
            raise ValueError('Unsupported filesystem type.')
    except subprocess.CalledProcessError as e:
        messagebox.showerror('Error', f'Failed to format drive {drive}.\n{e}')
        return False
    return True

def extract_img(img_path, temp_dir):
    """Extract the IMG file to the TEMP directory."""
    try:
        subprocess.run(['sudo', 'mcopy', '-i', img_path, '-s', '*', temp_dir], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror('Error', f'Failed to extract {img_path}.\n{e}')
        return False
    return True

def copy_files(src_dir, dest_dir):
    """Copy files from source to destination."""
    try:
        for item in os.listdir(src_dir):
            s = os.path.join(src_dir, item)
            d = os.path.join(dest_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, False, shutil.copy2)
            else:
                shutil.copy2(s, d)
    except Exception as e:
        messagebox.showerror('Error', f'Failed to copy files.\n{e}')
        return False
    return True

def on_start_installation():
    def run_installation():
        """Function to run the installation process."""
        drive = drive_var.get()
        if not drive:
            messagebox.showerror('Error', 'No drive selected.')
            return

        partitions = get_partitions(drive)
        if len(partitions) > 1:
            messagebox.showwarning('Multiple Partitions Detected',
                                   'This drive has multiple partitions! Please use "GPARTED" to format to a single empty partition. This app will automatically format the drive but you must have a single partition so please format to a single empty unpartitioned partition.')
            return

        fs_type = fs_type_var.get()
        if fs_type not in ['FAT16', 'FAT32']:
            messagebox.showerror('Error', 'Invalid filesystem type.')
            return

        if not format_drive(drive, fs_type):
            return

        temp_dir = 'TEMP'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        img_path = 'win3.1.img'
        if not extract_img(img_path, temp_dir):
            return

        if not copy_files(temp_dir, drive):
            return

        # Update progress bar to 100%
        progress_var.set(100)
        progress_bar.update()

        messagebox.showinfo('Success', 'Installation complete.')
        progress_window.destroy()

    # Create and show the progress window
    progress_window = tk.Toplevel(root)
    progress_window.title('Installation Progress')
    progress_window.geometry('300x100')
    
    progress_var = tk.DoubleVar()
    progress_var.set(0)
    progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
    progress_bar.pack(pady=20, padx=20, fill='x')

    # Run installation in a separate thread to avoid blocking the GUI
    threading.Thread(target=run_installation).start()

def show_info_slideshow():
    """Create a slideshow window displaying informational text."""
    def update_text():
        nonlocal quote_index
        if quote_index >= len(quotes):
            quote_index = 0
        info_label.config(text=quotes[quote_index])
        quote_index += 1
        root.after(3000, update_text)  # Update every 3 seconds

    quotes = [
        "The Windows 3.1 installer allows you to install a preconfigured Windows image. This is a fully patched, fully working Windows 3.1 image that you can install on modern hardware!",
        "Windows 3.1 installer is licensed under BSD Clause 3.",
        "The Windows 3.1 installer installs Windows 3.1 without floppies or any hassle. You can install and remove apps you like and don't like.",
        "This project is just for fun. Windows 3.1's rights go to Microsoft. I am just making this project for fun! No hassle setup.",
        "Did you know, Windows 3.1 is more stable than 9x? If you'd like to install 9x on your PC, you can check out https://github.com/oerg866/win98-quickinstall. It allows you to install Windows 9X on any hardware!",
        "Windows 3.1 was the successor to Windows 3.0, Windows 3.1 made Windows 3.0 more stable and less buggy. Windows 3.1 is less frequently talked about. For all you Windows 3.1 fans out there, this tool is for you!",
        "Windows 3.1 was not only stable but is pretty easy to use! This installer will do all the heavy lifting for you. You just install the required packages and boom! You are good to go!"
    ]
    
    quote_index = 0
    info_window = tk.Toplevel(root)
    info_window.title('Information')
    info_window.geometry('600x200')

    info_label = tk.Label(info_window, text="", wraplength=500, justify="left")
    info_label.pack(pady=20, padx=20)

    update_text()  # Start the slideshow

# Ensure the script is run with sudo
ensure_sudo()

# Check required system packages and install if missing
missing_system_packages = check_required_packages()
if missing_system_packages:
    install_required_packages(missing_system_packages)

# Check required Python packages
missing_python_packages = check_python_packages()
if missing_python_packages:
    messagebox.showinfo('Missing Python Packages',
                        f'The following Python packages are missing: {", ".join(missing_python_packages)}.\nPlease install them using pip.')
    if missing_python_packages:
        install_python_packages(missing_python_packages)

# Check if there are any remaining missing Python packages after attempted installation
missing_python_packages = check_python_packages()
if missing_python_packages:
    messagebox.showerror('Error', f'The following Python packages could not be installed: {", ".join(missing_python_packages)}. Please install them manually and rerun the script.')
    sys.exit()

# Set up the main GUI
root = tk.Tk()
root.title('Windows 3.1 Installer')

label = tk.Label(root, text='Welcome to the Windows 3.1 Installer')
label.pack(pady=10)

# Drive selection
drive_var = tk.StringVar()
all_drives = get_all_drives()
removable_drives = get_removable_drives()

if not all_drives:
    messagebox.showerror('Error', 'No /dev/sdX drives found.')
    root.destroy()
else:
    drive_choices = [(drive, 'disabled' if drive == '/dev/sda' else 'normal') for drive in all_drives]
    
    def on_drive_selection(event):
        selected_drive = drive_var.get()
        if selected_drive == '/dev/sda':
            messagebox.showwarning('Drive Not Allowed', 'Selection of /dev/sda is not permitted.')
            drive_var.set('')

    drive_label = tk.Label(root, text='Select a drive:')
    drive_label.pack(pady=5)
    
    drive_menu = ttk.Combobox(root, textvariable=drive_var, values=[d[0] for d in drive_choices])
    drive_menu.pack(pady=5)
    drive_menu.set('Select a drive')
    drive_menu.bind('<<ComboboxSelected>>', on_drive_selection)

# Filesystem type selection
fs_type_var = tk.StringVar(value='FAT32')
fs_type_label = tk.Label(root, text='Select filesystem type:')
fs_type_label.pack(pady=5)

fs_type_menu = ttk.Combobox(root, textvariable=fs_type_var, values=['FAT16', 'FAT32'])
fs_type_menu.pack(pady=5)

# Start button
start_button = tk.Button(root, text='Start Installation', command=lambda: [show_info_slideshow(), on_start_installation()])
start_button.pack(pady=20)

root.mainloop()

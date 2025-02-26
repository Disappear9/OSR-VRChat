import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import yaml
import serial.tools.list_ports
import subprocess
from tkinter import messagebox


# Function to load the current settings from the YAML file
def load_settings():
    with open("settings-advanced-v0.2.2.yaml", "r") as file:
        settings = yaml.safe_load(file)
    return settings


# Function to save the settings back to the YAML file
def save_settings():
    try:
        # Validate the inputs
        max_pos = int(max_pos_var.get())
        min_pos = int(min_pos_var.get())
        if not (0 <= max_pos <= 1000):
            raise ValueError("Max position must be between 0 and 1000.")
        if not (0 <= min_pos <= 1000):
            raise ValueError("Min position must be between 0 and 1000.")
        if min_pos >= max_pos:
            raise ValueError("Min position must be lower than Max position.")
        
        settings['osr2']['user_type'] = user_type_var.get()
        settings['osr2']['objective'] = objective_var.get()
        settings['osr2']['max_pos'] = max_pos
        settings['osr2']['min_pos'] = min_pos
        settings['osr2']['com_port'] = com_port_var.get()
        settings['osr2']['max_velocity'] = int(max_velocity_var.get())
        settings['osr2']['updates_per_second'] = int(updates_per_second_var.get())

        with open("settings-advanced-v0.2.2.yaml", "w") as file:
            yaml.dump(settings, file)

        show_message("成功保存Changes saved successfully!", "success")
    except ValueError as ve:
        show_message(str(ve), "error")


# Function to display success or error messages
def show_message(message, msg_type):
    if msg_type == "success":
        message_label.config(text=message, fg="green")
    elif msg_type == "error":
        message_label.config(text=message, fg="red")


# Function to get all available COM ports
def get_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


# Function to run the main program
def run_main_program():
    subprocess.run(["python", "omain.py"])


# Function to switch between English and Chinese
def switch_language():
    if language_var.get() == "English":
        language_var.set("Chinese")
        update_ui_language("Chinese")
    else:
        language_var.set("English")
        update_ui_language("English")


# Function to update the UI language
def update_ui_language(language):
    if language == "English":
        user_type_label.config(text="User Type (Inserting or Inserted):")
        objective_label.config(text="Objective (Self or Others):")
        max_pos_label.config(text="Max Position (0-1000):")
        min_pos_label.config(text="Min Position (0-1000):")
        com_port_label.config(text="COM Port:")
        max_velocity_label.config(text="Max Velocity (0-1000):")
        updates_per_second_label.config(text="Updates per Second (0-100):")
        save_button.config(text="Save Changes")
        run_button.config(text="Run Main Program")
        language_button.config(text="Switch to Chinese")
        user_type_menu['values'] = ["inserting", "inserted"]
        objective_menu['values'] = ["self", "others"]
        user_type_var.set("inserting")  # Default value
        objective_var.set("self")      # Default value
    else:
        user_type_label.config(text="用户类型（插入或被插入）：")
        objective_label.config(text="目标（自我或他人）：")
        max_pos_label.config(text="最大位置（0-1000）：")
        min_pos_label.config(text="最小位置（0-1000）：")
        com_port_label.config(text="COM端口：")
        max_velocity_label.config(text="最大速度（0-1000）：")
        updates_per_second_label.config(text="每秒更新（0-100）：")
        save_button.config(text="保存更改")
        run_button.config(text="运行主程序")
        language_button.config(text="切换到英文")
        user_type_menu['values'] = ["插入", "被插入"]
        objective_menu['values'] = ["自我", "他人"]
        user_type_var.set("插入")  # Default value
        objective_var.set("自我")  # Default value


# Load initial settings
settings = load_settings()

# Create the main window with a theme
root = ThemedTk(theme="arc")
root.title("OSC and Motion Settings")

# Change the font size for all widgets
style = ttk.Style(root)
style.configure('.', font=('Helvetica', 12))  # Set default font size to 12 for all widgets

# Apply the same font to Entry and Combobox widgets explicitly
root.option_add('*TButton*font', ('Helvetica', 12))  # Button font
root.option_add('*TLabel*font', ('Helvetica', 12))   # Label font
root.option_add('*TEntry*font', ('Helvetica', 12))   # Entry font
root.option_add('*TCombobox*font', ('Helvetica', 12))  # Combobox font

# Variables for the settings
user_type_var = tk.StringVar(value=settings['osr2']['user_type'])
objective_var = tk.StringVar(value=settings['osr2']['objective'])
max_pos_var = tk.StringVar(value=str(settings['osr2']['max_pos']))
min_pos_var = tk.StringVar(value=str(settings['osr2']['min_pos']))
com_port_var = tk.StringVar(value=settings['osr2']['com_port'])
max_velocity_var = tk.StringVar(value=str(settings['osr2']['max_velocity']))
updates_per_second_var = tk.StringVar(value=str(settings['osr2']['updates_per_second']))

# Language selection variable
language_var = tk.StringVar(value="Chinese")

# User Interface Elements
user_type_label = ttk.Label(root, text="User Type (Inserting or Inserted):")
user_type_label.pack(padx=10, pady=5)
user_type_menu = ttk.Combobox(root, textvariable=user_type_var, values=["inserting", "inserted"], state="readonly")
user_type_menu.pack(padx=10, pady=5)

objective_label = ttk.Label(root, text="Objective (Self or Others):")
objective_label.pack(padx=10, pady=5)
objective_menu = ttk.Combobox(root, textvariable=objective_var, values=["self", "others"], state="readonly")
objective_menu.pack(padx=10, pady=5)

max_pos_label = ttk.Label(root, text="Max Position (0-1000):")
max_pos_label.pack(padx=10, pady=5)
max_pos_entry = ttk.Entry(root, textvariable=max_pos_var)
max_pos_entry.pack(padx=10, pady=5)

min_pos_label = ttk.Label(root, text="Min Position (0-1000):")
min_pos_label.pack(padx=10, pady=5)
min_pos_entry = ttk.Entry(root, textvariable=min_pos_var)
min_pos_entry.pack(padx=10, pady=5)

com_port_label = ttk.Label(root, text="COM Port:")
com_port_label.pack(padx=10, pady=5)
com_port_menu = ttk.Combobox(root, textvariable=com_port_var, values=get_com_ports(), state="readonly")
com_port_menu.pack(padx=10, pady=5)

max_velocity_label = ttk.Label(root, text="Max Velocity (0-1000):")
max_velocity_label.pack(padx=10, pady=5)
max_velocity_entry = ttk.Entry(root, textvariable=max_velocity_var)
max_velocity_entry.pack(padx=10, pady=5)

updates_per_second_label = ttk.Label(root, text="Updates per Second (0-100):")
updates_per_second_label.pack(padx=10, pady=5)
updates_per_second_entry = ttk.Entry(root, textvariable=updates_per_second_var)
updates_per_second_entry.pack(padx=10, pady=5)

# Message Label for success/error
message_label = tk.Label(root, text="", font=('Helvetica', 10))
message_label.pack(padx=10, pady=5)

# Buttons
save_button = ttk.Button(root, text="Save Changes", command=save_settings)
save_button.pack(padx=10, pady=10)

run_button = ttk.Button(root, text="Run Main Program", command=run_main_program)
run_button.pack(padx=10, pady=10)

language_button = ttk.Button(root, text="Switch to Chinese", command=switch_language)
language_button.pack(padx=10, pady=10)

# Run the application
root.mainloop()

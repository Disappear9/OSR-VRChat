import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import yaml
import serial.tools.list_ports
from ttkthemes import ThemedTk

# Translation dictionaries for UI labels and messages
translations = {
    'en': {
        'user_type': 'User Type',
        'objective': 'Objective',
        'max_pos': 'Max Position',
        'min_pos': 'Min Position',
        'com_port': 'COM Port',
        'max_velocity': 'Max Velocity',
        'updates_per_second': 'Updates per Second',
        'save': 'Save',
        'run_main': 'Run Main',
        'language': '切换中文',
        'debug_toggle': 'Toggle Debug',
        'success': 'Changes saved successfully',
        'error': 'Illegal input',
        'user_type_error': 'Invalid User Type.',
        'objective_error': 'Invalid Objective.',
        'max_pos_error': 'Max Position must be between 0 and 1000.',
        'min_pos_error': 'Min Position must be between 0 and 1000, and lower than Max Position.',
        'com_port_error': 'Invalid COM Port.',
        'max_velocity_error': 'Max Velocity must be between 0 and 1000.',
        'updates_per_second_error': 'Updates per Second must be between 0 and 100.',
        # Drop-down options (saved value is always english)
        'inserting': 'inserting',
        'inserted': 'inserted',
        'self': 'self',
        'others': 'others'
    },
    'zh': {
        'user_type': '用户类型',
        'objective': '目标',
        'max_pos': '最大位置',
        'min_pos': '最小位置',
        'com_port': '串口',
        'max_velocity': '最大速度',
        'updates_per_second': '每秒更新数',
        'save': '保存',
        'run_main': '运行主程序',
        'language': 'English Version',
        'debug_toggle': '显示调试信息',
        'success': '保存成功',
        'error': '输入非法',
        'user_type_error': '无效的用户类型。',
        'objective_error': '无效的目标。',
        'max_pos_error': '最大位置必须介于0和1000之间。',
        'min_pos_error': '最小位置必须介于0和1000之间，并且小于最大位置。',
        'com_port_error': '无效的端口。',
        'max_velocity_error': '最大速度必须介于0和1000之间。',
        'updates_per_second_error': '每秒更新数必须介于0和100之间。',
        # Drop-down options (displayed value translated but saved in english)
        'inserting': '插入',
        'inserted': '已插入',
        'self': '自我',
        'others': '他人'
    }
}

class ParameterEditor:
    def __init__(self, master):
        self.master = master
        self.current_language = 'zh'
        self.settings_file = "settings-advanced-v0.2.2.yaml"
        self.load_settings()

        # Mapping for drop-down options.
        # The key is the english value that will be saved.
        self.user_type_mapping = {
            'inserting': {'en': 'inserting', 'zh': '插入'},
            'inserted': {'en': 'inserted', 'zh': '被插入'}
        }
        self.objective_mapping = {
            'self': {'en': 'self', 'zh': '自己'},
            'others': {'en': 'others', 'zh': '别人'}
        }

        # Global font size variable and font configuration.
        self.font_size = tk.IntVar(value=13)
        self.custom_font = tkFont.Font(family="Helvetica", size=self.font_size.get())
        self.font_size.trace_add("w", self.update_font)

        self.create_widgets()

    def load_settings(self):
        with open(self.settings_file, "r", encoding="utf-8") as f:
            self.settings = yaml.safe_load(f)
        # Get the section with parameters to be modified
        self.osr2 = self.settings.get("osr2", {})

    def create_widgets(self):
        self.master.title("Parameter Editor")

        # Main frame for parameter inputs and controls
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=15)

        row = 0
        # # Font size control
        # ttk.Label(self.main_frame, text="Font Size:", font=self.custom_font).grid(row=row, column=0, sticky="w", pady=5)
        # self.font_size_spinbox = ttk.Spinbox(self.main_frame, from_=8, to=32, textvariable=self.font_size, width=5)
        # self.font_size_spinbox.grid(row=row, column=1, sticky="w", pady=5)
        # row += 1

        # User Type (drop-down, readonly)
        self.label_user_type = ttk.Label(self.main_frame, text=translations[self.current_language]['user_type'], font=self.custom_font)
        self.label_user_type.grid(row=row, column=0, sticky="w", pady=5)
        self.user_type_var = tk.StringVar()
        user_type_value = self.osr2.get("user_type", "inserting")
        if user_type_value not in self.user_type_mapping:
            user_type_value = "inserting"
        self.user_type_var.set(self.get_display_value("user_type", user_type_value))
        self.user_type_combobox = ttk.Combobox(self.main_frame, textvariable=self.user_type_var, state="readonly", font=self.custom_font)
        self.user_type_combobox['values'] = [self.user_type_mapping[k][self.current_language] for k in self.user_type_mapping]
        self.user_type_combobox.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Objective (drop-down, readonly)
        self.label_objective = ttk.Label(self.main_frame, text=translations[self.current_language]['objective'], font=self.custom_font)
        self.label_objective.grid(row=row, column=0, sticky="w", pady=5)
        self.objective_var = tk.StringVar()
        objective_value = self.osr2.get("objective", "self")
        if objective_value not in self.objective_mapping:
            objective_value = "self"
        self.objective_var.set(self.get_display_value("objective", objective_value))
        self.objective_combobox = ttk.Combobox(self.main_frame, textvariable=self.objective_var, state="readonly", font=self.custom_font)
        self.objective_combobox['values'] = [self.objective_mapping[k][self.current_language] for k in self.objective_mapping]
        self.objective_combobox.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Maximum Position
        self.label_max_pos = ttk.Label(self.main_frame, text=translations[self.current_language]['max_pos'], font=self.custom_font)
        self.label_max_pos.grid(row=row, column=0, sticky="w", pady=5)
        self.max_pos_var = tk.StringVar(value=str(self.osr2.get("max_pos", 900)))
        self.entry_max_pos = ttk.Entry(self.main_frame, textvariable=self.max_pos_var, font=self.custom_font)
        self.entry_max_pos.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Minimum Position
        self.label_min_pos = ttk.Label(self.main_frame, text=translations[self.current_language]['min_pos'], font=self.custom_font)
        self.label_min_pos.grid(row=row, column=0, sticky="w", pady=5)
        self.min_pos_var = tk.StringVar(value=str(self.osr2.get("min_pos", 100)))
        self.entry_min_pos = ttk.Entry(self.main_frame, textvariable=self.min_pos_var, font=self.custom_font)
        self.entry_min_pos.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # COM Port (drop-down, readonly)
        self.label_com_port = ttk.Label(self.main_frame, text=translations[self.current_language]['com_port'], font=self.custom_font)
        self.label_com_port.grid(row=row, column=0, sticky="w", pady=5)
        self.com_port_var = tk.StringVar()
        self.available_ports = self.get_available_com_ports()
        com_port_value = self.osr2.get("com_port", self.available_ports[0] if self.available_ports else "")
        if com_port_value not in self.available_ports and self.available_ports:
            com_port_value = self.available_ports[0]
        self.com_port_var.set(com_port_value)
        self.com_port_combobox = ttk.Combobox(self.main_frame, textvariable=self.com_port_var, values=self.available_ports, state="readonly", font=self.custom_font)
        self.com_port_combobox.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Maximum Velocity
        self.label_max_velocity = ttk.Label(self.main_frame, text=translations[self.current_language]['max_velocity'], font=self.custom_font)
        self.label_max_velocity.grid(row=row, column=0, sticky="w", pady=5)
        self.max_velocity_var = tk.StringVar(value=str(self.osr2.get("max_velocity", 300)))
        self.entry_max_velocity = ttk.Entry(self.main_frame, textvariable=self.max_velocity_var, font=self.custom_font)
        self.entry_max_velocity.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Updates per Second
        self.label_updates_per_second = ttk.Label(self.main_frame, text=translations[self.current_language]['updates_per_second'], font=self.custom_font)
        self.label_updates_per_second.grid(row=row, column=0, sticky="w", pady=5)
        self.ups_var = tk.StringVar(value=str(self.osr2.get("updates_per_second", 40)))
        self.entry_ups = ttk.Entry(self.main_frame, textvariable=self.ups_var, font=self.custom_font)
        self.entry_ups.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Action Buttons
        self.save_button = ttk.Button(self.main_frame, text=translations[self.current_language]['save'], command=self.save_settings, style="Accent.TButton")
        self.save_button.grid(row=row, column=0, pady=15)
        self.run_button = ttk.Button(self.main_frame, text=translations[self.current_language]['run_main'], command=self.run_main_program)
        self.run_button.grid(row=row, column=1, pady=15)
        row += 1

        self.lang_button = ttk.Button(self.main_frame, text=translations[self.current_language]['language'], command=self.switch_language)
        self.lang_button.grid(row=row, column=0, pady=15)
        self.debug_toggle_button = ttk.Button(self.main_frame, text=translations[self.current_language]['debug_toggle'], command=self.toggle_debug)
        self.debug_toggle_button.grid(row=row, column=1, pady=15)
        row += 1

        # Message label for success/error feedback
        self.message_label = ttk.Label(self.main_frame, text="", font=self.custom_font)
        self.message_label.grid(row=row, column=0, columnspan=2)

        # Debug messages area (on the right)
        self.debug_frame = ttk.Frame(self.master)
        self.debug_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=15)
        self.debug_text = tk.Text(self.debug_frame, width=40, height=20, font=self.custom_font)
        self.debug_text.pack(expand=True, fill="both")
        self.debug_visible = True

        # Configure grid weights for resizing
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=0)
        self.master.rowconfigure(0, weight=1)

    def get_available_com_ports(self):
        # List available COM ports (fallback to a sample list if none found)
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports] if ports else ["COM1", "COM2", "COM3", "COM4"]

    def get_display_value(self, field, english_value):
        # Return the text to be shown in the drop-down based on the current language
        if field == "user_type":
            return self.user_type_mapping.get(english_value, {}).get(self.current_language, english_value)
        elif field == "objective":
            return self.objective_mapping.get(english_value, {}).get(self.current_language, english_value)
        return english_value

    def get_english_value(self, field, display_value):
        # Convert the displayed text back to its english key for saving
        if field == "user_type":
            for key, mapping in self.user_type_mapping.items():
                if mapping[self.current_language] == display_value:
                    return key
        elif field == "objective":
            for key, mapping in self.objective_mapping.items():
                if mapping[self.current_language] == display_value:
                    return key
        return display_value

    def switch_language(self):
        # Toggle between English and Chinese and update all labels and drop-down options.
        self.current_language = 'zh' if self.current_language == 'en' else 'en'
        self.label_user_type.config(text=translations[self.current_language]['user_type'])
        self.label_objective.config(text=translations[self.current_language]['objective'])
        self.label_max_pos.config(text=translations[self.current_language]['max_pos'])
        self.label_min_pos.config(text=translations[self.current_language]['min_pos'])
        self.label_com_port.config(text=translations[self.current_language]['com_port'])
        self.label_max_velocity.config(text=translations[self.current_language]['max_velocity'])
        self.label_updates_per_second.config(text=translations[self.current_language]['updates_per_second'])
        self.save_button.config(text=translations[self.current_language]['save'])
        self.run_button.config(text=translations[self.current_language]['run_main'])
        self.lang_button.config(text=translations[self.current_language]['language'])
        self.debug_toggle_button.config(text=translations[self.current_language]['debug_toggle'])
        # Update drop-down list values and current selections.
        self.user_type_combobox['values'] = [self.user_type_mapping[k][self.current_language] for k in self.user_type_mapping]
        english_ut = self.get_english_value("user_type", self.user_type_var.get())
        self.user_type_var.set(self.get_display_value("user_type", english_ut))
        self.objective_combobox['values'] = [self.objective_mapping[k][self.current_language] for k in self.objective_mapping]
        english_obj = self.get_english_value("objective", self.objective_var.get())
        self.objective_var.set(self.get_display_value("objective", english_obj))
        self.message_label.config(text="")

    def update_font(self, *args):
        # Update the custom font size across widgets when the font size variable changes.
        new_size = self.font_size.get()
        self.custom_font.config(size=new_size)

    def save_settings(self):
        # Validate and save the settings to the YAML file.
        error_message = ""
        valid = True

        # Validate fields
        try:
            max_pos = int(self.max_pos_var.get())
            if not (0 <= max_pos <= 1000):
                error_message = translations[self.current_language]['max_pos_error']
                valid = False
        except ValueError:
            error_message = translations[self.current_language]['max_pos_error']
            valid = False

        try:
            min_pos = int(self.min_pos_var.get())
            if not (0 <= min_pos <= 1000) or min_pos >= max_pos:
                error_message = translations[self.current_language]['min_pos_error']
                valid = False
        except ValueError:
            error_message = translations[self.current_language]['min_pos_error']
            valid = False

        try:
            max_velocity = int(self.max_velocity_var.get())
            if not (0 <= max_velocity <= 1000):
                error_message = translations[self.current_language]['max_velocity_error']
                valid = False
        except ValueError:
            error_message = translations[self.current_language]['max_velocity_error']
            valid = False

        try:
            ups = int(self.ups_var.get())
            if not (0 <= ups <= 100):
                error_message = translations[self.current_language]['updates_per_second_error']
                valid = False
        except ValueError:
            error_message = translations[self.current_language]['updates_per_second_error']
            valid = False

        com_port = self.com_port_var.get()
        if com_port not in self.available_ports:
            error_message = translations[self.current_language]['com_port_error']
            valid = False

        if not valid:
            self.show_message(error_message, "red")
            return

        # Get the english values for drop-down selections.
        user_type = self.get_english_value("user_type", self.user_type_var.get())
        objective = self.get_english_value("objective", self.objective_var.get())

        # Update the settings dictionary.
        self.osr2["user_type"] = user_type
        self.osr2["objective"] = objective
        self.osr2["max_pos"] = max_pos
        self.osr2["min_pos"] = min_pos
        self.osr2["com_port"] = com_port
        self.osr2["max_velocity"] = max_velocity
        self.osr2["updates_per_second"] = ups

        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.settings, f, allow_unicode=True)
            self.show_message(translations[self.current_language]['success'], "green")
        except Exception as e:
            self.show_message(translations[self.current_language]['error'], "red")

    def show_message(self, msg, color):
        self.message_label.config(text=msg, foreground=color)

    def run_main_program(self):
        # Run the main program (omain.py) in a separate thread so the UI remains responsive.
        thread = threading.Thread(target=self.run_main_thread)
        thread.daemon = True
        thread.start()

    def run_main_thread(self):
        # Launch omain.py and stream its output to the debug text area.
        process = subprocess.Popen(
            ["python", "omain.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in process.stdout:
            self.append_debug(line)
        process.stdout.close()
        process.wait()

    def append_debug(self, text):
        # Append text to the debug messages widget (thread-safe update)
        def inner():
            self.debug_text.insert(tk.END, text)
            self.debug_text.see(tk.END)
        self.master.after(0, inner)

    def toggle_debug(self):
        if self.debug_visible: 
            self.debug_frame.grid_remove() 
            self.debug_visible = False 
        else: 
            self.debug_frame.grid() 
            self.debug_visible = True
        

root = ThemedTk(theme="arc") 
app = ParameterEditor(root) 
root.mainloop()


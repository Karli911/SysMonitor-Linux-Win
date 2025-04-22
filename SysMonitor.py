# This script is a simple system monitor that displays CPU, RAM, Disk, Network usage and CPU temperature.
# It also shows battery status for Linux and Windows systems. 
import tkinter as tk
import psutil
import threading
import time
import sys
import os
import platform

class SystemMonitor:
     
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor")
        self.root.geometry("336x278")
        self.root.resizable(False, False)

        # System info labels
        self.cpu_label = tk.Label(root, text="CPU: ", font=("Helvetica", 12))
        self.cpu_label.pack(pady=5)

        self.ram_label = tk.Label(root, text="RAM: ", font=("Helvetica", 12))
        self.ram_label.pack(pady=5)

        self.disk_label = tk.Label(root, text="Disk: ", font=("Helvetica", 12))
        self.disk_label.pack(pady=5)

        self.net_label = tk.Label(root, text="Network: ", font=("Helvetica", 12))
        self.net_label.pack(pady=5)

        self.temp_label = tk.Label(root, text="Temperature: ", font=("Helvetica", 12))
        self.temp_label.pack(pady=5)

        # Detect platform
        self.os_type = platform.system()

        # Battery section
        batt_frame = tk.LabelFrame(root, text="Battery Status", font=("Helvetica", 10, "bold"))
        batt_frame.pack(padx=10, pady=5, fill="both")

        self.battery_labels = []

        if self.os_type == "Linux":
            # Get list of BAT* devices
            self.batteries = [b for b in os.listdir("/sys/class/power_supply/") if b.startswith("BAT")]
        elif self.os_type == "Windows":
            self.batteries = ["BATTERY"]  # Just one placeholder for psutil
        else:
            self.batteries = []

        # Create labels for each battery
        for bname in self.batteries:
            label = tk.Label(batt_frame, text=f"{bname}: ", font=("Helvetica", 12))
            label.pack(pady=3)
            self.battery_labels.append((bname, label))

        self.update_data()

    def secs2hours(self, secs):
        mm, ss = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        return f"{int(hh)}:{int(mm):02}:{int(ss):02}"


    def read_battery_status(self, battery_name):
        base_path = f"/sys/class/power_supply/{battery_name}/"
        try:
            with open(base_path + "capacity", "r") as f:
                percent = int(f.read().strip())

            with open(base_path + "status", "r") as f:
                status = f.read().strip()

            energy_now = energy_full = power_now = None

            if os.path.exists(base_path + "energy_now"):
                with open(base_path + "energy_now", "r") as f:
                    energy_now = int(f.read().strip())

            if os.path.exists(base_path + "energy_full"):
                with open(base_path + "energy_full", "r") as f:
                    energy_full = int(f.read().strip())

            if os.path.exists(base_path + "power_now"):
                with open(base_path + "power_now", "r") as f:
                    power_now = int(f.read().strip())

            time_str = "?"

            if energy_now is not None and power_now and power_now != 0:
                if status == "Discharging":
                    seconds = int(3600 * energy_now / power_now)
                    time_str = self.secs2hours(seconds)
                elif status == "Charging" and energy_full is not None:
                    energy_needed = energy_full - energy_now
                    seconds = int(3600 * energy_needed / power_now)
                    time_str = self.secs2hours(seconds)

            return percent, status, time_str

        except Exception as e:
            print(f"Error reading battery {battery_name}: {e}")
            return None, None, None
    
    
    def style_battery_label(self, label, percent):
        if percent > 75:
            label.config(fg="green")
        elif percent > 30:
            label.config(fg="orange")
        else:
            label.config(fg="red")
    
    
     
    def update_data(self):
        # CPU, RAM, Disk, Network
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        net_sent = net.bytes_sent / (1024 * 1024)
        net_recv = net.bytes_recv / (1024 * 1024)

        # Temperature
        temp = psutil.sensors_temperatures(fahrenheit=False)

        self.cpu_label.config(text=f"CPU: {cpu}%")
        self.ram_label.config(text=f"RAM: {ram}%")
        self.disk_label.config(text=f"Disk: {disk}%")
        self.net_label.config(text=f"Upload: {net_sent:.2f} MB | Download: {net_recv:.2f} MB")

        if temp and 'coretemp' in temp:
            self.temp_label.config(text=f"Temperature: {temp['coretemp'][0].current:.1f}°C")
        else:
            self.temp_label.config(text="Temperature: N/A")

        # Battery update
        batt = None
        if self.os_type == "Windows":
            batt = psutil.sensors_battery()

        for bname, label in self.battery_labels:
            if self.os_type == "Linux":
                percent, status, time_str = self.read_battery_status(bname)
            elif self.os_type == "Windows":
                batt = psutil.sensors_battery()
                if batt is not None:
                    percent = round(batt.percent, 2)
                    status = "Charging" if batt.power_plugged else "Discharging"
                    time_str = self.secs2hours(batt.secsleft) if batt.secsleft != psutil.POWER_TIME_UNLIMITED else "∞"
                else:
                    percent, status, time_str = None, None, None
            else:
                percent, status, time_str = None, None, None

            if percent is not None:
                icon = "🔌" if "Charging" in status else "⚡"
                if time_str and "Discharging" in status and time_str != "?":
                    time_display = f"| {time_str} left"
                else:
                    time_display = ""
                label.config(text=f"{bname}: {percent}% {icon} ({status}) {time_display}")
                self.style_battery_label(label, percent)
            else:
                label.config(text=f"{bname}: N/A", fg="gray")

        # ✅ Schedule next update once, not per battery
        self.root.after(2000, self.update_data)


if __name__ == "__main__":
    root = tk.Tk()
    app = SystemMonitor(root)
    root.mainloop()




##### ----------------- | Documentation Links | ----------------- #####
# Psutil documentation: https://psutil.readthedocs.io/en/latest/
# Tkinter documentation: https://docs.python.org/3/library/tkinter.html
# Os documentation: https://docs.python.org/3/library/os.html
# Threading documentation: https://docs.python.org/3/library/threading.html
# Time documentation: https://docs.python.org/3/library/time.html
# Sys documentation: https://docs.python.org/3/library/sys.html
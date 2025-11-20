import customtkinter
import psutil
import platform
import threading
import time
import datetime
import subprocess # Vamos usar isso no lugar do GPUtil

# Configurações iniciais
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor de Sistema")
        self.geometry("450x550")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Título
        self.title_label = customtkinter.CTkLabel(self.main_frame, text="Monitor de Hardware", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(10, 20))

        # CPU
        self.cpu_frame = customtkinter.CTkFrame(self.main_frame)
        self.cpu_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.cpu_label = customtkinter.CTkLabel(self.cpu_frame, text="CPU Uso: 0%", font=("", 14))
        self.cpu_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.cpu_progress = customtkinter.CTkProgressBar(self.cpu_frame, orientation="horizontal")
        self.cpu_progress.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.cpu_progress.set(0)

        # RAM
        self.ram_frame = customtkinter.CTkFrame(self.main_frame)
        self.ram_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.ram_label = customtkinter.CTkLabel(self.ram_frame, text="RAM Uso: 0% (0/0 GB)", font=("", 14))
        self.ram_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ram_progress = customtkinter.CTkProgressBar(self.ram_frame, orientation="horizontal")
        self.ram_progress.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.ram_progress.set(0)

        # GPU
        self.gpu_frame = customtkinter.CTkFrame(self.main_frame)
        self.gpu_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.gpu_label = customtkinter.CTkLabel(self.gpu_frame, text="GPU: Buscando...", font=("", 14))
        self.gpu_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.gpu_progress = customtkinter.CTkProgressBar(self.gpu_frame, orientation="horizontal")
        self.gpu_progress.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.gpu_progress.set(0)
        self.gpu_temp_label = customtkinter.CTkLabel(self.gpu_frame, text="Temp: --", font=("", 12))
        self.gpu_temp_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        # Sistema
        self.sys_info_frame = customtkinter.CTkFrame(self.main_frame)
        self.sys_info_frame.grid(row=4, column=0, padx=10, pady=(15, 5), sticky="ew")
        self.os_label = customtkinter.CTkLabel(self.sys_info_frame, text=f"OS: {platform.system()} {platform.release()}", font=("", 12))
        self.os_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")
        self.uptime_label = customtkinter.CTkLabel(self.sys_info_frame, text="Uptime: ...", font=("", 12))
        self.uptime_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        # Iniciar Thread
        self.stop_event = threading.Event()
        self.monitor_thread = threading.Thread(target=self.update_data, daemon=True)
        self.monitor_thread.start()

    def pegar_gpu_nvidia(self):
        """Lê dados da NVIDIA sem abrir janela preta"""
        try:
            # Configurações para SUFOCAR a janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Chama o nvidia-smi diretamente
            cmd = ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,name', '--format=csv,noheader,nounits']
            
            # creationflags=0x08000000 é o segredo (CREATE_NO_WINDOW)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 startupinfo=startupinfo, creationflags=0x08000000)
            
            output, _ = p.communicate()
            dados = output.decode('utf-8').strip().split(',')
            
            if len(dados) >= 3:
                return {
                    'load': float(dados[0]),
                    'temp': float(dados[1]),
                    'name': dados[2].strip()
                }
        except:
            return None
        return None

    def on_closing(self):
        self.stop_event.set()
        self.destroy()

    def update_data(self):
        while not self.stop_event.is_set():
            # 1. CPU
            cpu_pct = psutil.cpu_percent(interval=None)
            self.cpu_label.configure(text=f"CPU Uso: {cpu_pct:.1f}%")
            self.cpu_progress.set(cpu_pct / 100)

            # 2. RAM
            ram = psutil.virtual_memory()
            ram_used = ram.used / (1024**3)
            ram_total = ram.total / (1024**3)
            self.ram_label.configure(text=f"RAM Uso: {ram.percent:.1f}% ({ram_used:.1f}/{ram_total:.1f} GB)")
            self.ram_progress.set(ram.percent / 100)

            # 3. GPU (Seguro sem piscar)
            gpu_data = self.pegar_gpu_nvidia()
            if gpu_data:
                self.gpu_label.configure(text=f"GPU Uso: {gpu_data['load']:.1f}% ({gpu_data['name']})")
                self.gpu_progress.set(gpu_data['load'] / 100)
                self.gpu_temp_label.configure(text=f"Temp: {gpu_data['temp']}°C")
            else:
                self.gpu_label.configure(text="GPU: Não detectada")

            # 4. Uptime
            uptime = datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
            self.uptime_label.configure(text=f"Uptime: {str(uptime).split('.')[0]}")

            time.sleep(1)

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
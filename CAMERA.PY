import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading


def window_size_adjuster(width, height):
    if width>1200 or height>700:
        width/=2
        height/=2
        width, height = window_size_adjuster(width, height)
    return round(width), round(height)


def get_vegetation_profiles():
    """
    Retorna perfis pré-configurados para diferentes tipos de vegetação.
    Cada perfil contém valores HSV (min e max) para detecção específica.
    """
    profiles = {
        "Padrao": {
            "h_min": 40, "h_max": 100,
            "s_min": 60, "s_max": 255,
            "v_min": 1, "v_max": 160,
            "descricao": "Vegetação verde padrão (grama, folhas saudáveis)"
        },
        "Verde Escuro": {
            "h_min": 35, "h_max": 75,
            "s_min": 50, "s_max": 255,
            "v_min": 30, "v_max": 150,
            "descricao": "Floresta densa, vegetação sombreada"
        },
        "Verde Claro": {
            "h_min": 40, "h_max": 90,
            "s_min": 30, "s_max": 200,
            "v_min": 100, "v_max": 255,
            "descricao": "Brotos novos, grama clara, vegetação jovem"
        },
        "Amarelado": {
            "h_min": 20, "h_max": 50,
            "s_min": 50, "s_max": 255,
            "v_min": 100, "v_max": 255,
            "descricao": "Folhas secas, vegetação em outono"
        },
        "Marron": {
            "h_min": 0, "h_max": 30,
            "s_min": 50, "s_max": 255,
            "v_min": 50, "v_max": 200,
            "descricao": "Terra seca, folhas mortas, vegetação seca"
        },
        "Personalizado": {
            "h_min": 0, "h_max": 179,
            "s_min": 0, "s_max": 255,
            "v_min": 0, "v_max": 255,
            "descricao": "Ajuste manual via sliders"
        }
    }
    return profiles


def apply_profile(profile_name, profiles):
    """
    Aplica os valores do perfil selecionado aos sliders.
    Retorna o dicionário com os valores do perfil.
    """
    if profile_name in profiles:
        return profiles[profile_name]
    return profiles["Padrao"]


class VegetationDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detector de Vegetação - GS_IOT")
        self.root.geometry("1200x800")

        # Carregar perfis
        self.vegetation_profiles = get_vegetation_profiles()
        self.profile_names = list(self.vegetation_profiles.keys())
        self.current_profile_name = self.profile_names[0]

        # Variáveis de controle
        self.running = False
        self.cap = None
        self.hsv_sliders_created = False
        self.hsv_window = None
        self.use_camera = tk.BooleanVar(value=True)  # True = câmera, False = imagem
        self.static_image = None  # Imagem estática carregada

        # Criar interface
        self.create_widgets()

        # Iniciar câmera
        self.start_camera()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame esquerdo para lista de perfis
        left_frame = ttk.Frame(main_frame, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Label para lista de perfis
        ttk.Label(left_frame, text="Seleção de Perfil:", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # Listbox para perfis
        self.profile_listbox = tk.Listbox(left_frame, font=('Arial', 11), height=10)
        self.profile_listbox.pack(fill=tk.BOTH, expand=True)

        # Adicionar perfis à listbox
        for profile in self.profile_names:
            self.profile_listbox.insert(tk.END, profile)

        # Selecionar primeiro perfil
        self.profile_listbox.select_set(0)
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_change)

        # Separator
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=20)

        # Label para fonte de imagem
        ttk.Label(left_frame, text="Fonte de Imagem:", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # Checkbox para selecionar câmera ou imagem
        self.camera_checkbox = ttk.Checkbutton(
            left_frame,
            text="Usar Câmera",
            variable=self.use_camera,
            command=self.on_source_change
        )
        self.camera_checkbox.pack(pady=(0, 10))

        # Botão para importar imagem
        self.import_button = ttk.Button(
            left_frame,
            text="Importar Imagem",
            command=self.import_image
        )
        self.import_button.pack(fill=tk.X, pady=(0, 10))
        self.import_button.state(['disabled'])

        # Frame direito para visualização
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvas para imagem
        self.canvas = tk.Canvas(right_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Barra inferior
        bottom_frame = ttk.Frame(self.root, height=100)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Labels para informações
        info_frame = ttk.Frame(bottom_frame)
        info_frame.pack(fill=tk.X)

        # Perfil selecionado
        ttk.Label(info_frame, text="Perfil:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.profile_label = ttk.Label(info_frame, text=self.current_profile_name, font=('Arial', 12))
        self.profile_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))

        # Descrição do perfil
        ttk.Label(info_frame, text="Descrição:", font=('Arial', 12, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.description_label = ttk.Label(info_frame, text=self.vegetation_profiles[self.current_profile_name]["descricao"], font=('Arial', 12))
        self.description_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 30))

        # Porcentagem de cobertura
        ttk.Label(info_frame, text="Cobertura Vegetal:", font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.coverage_label = ttk.Label(info_frame, text="0.00%", font=('Arial', 12))
        self.coverage_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 30), pady=(10, 0))

        # Status da cobertura
        ttk.Label(info_frame, text="Status:", font=('Arial', 12, 'bold')).grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.status_label = ttk.Label(info_frame, text="--", font=('Arial', 12))
        self.status_label.grid(row=1, column=3, sticky=tk.W, padx=(0, 30), pady=(10, 0))

        # Botão para sliders HSV (apenas para Personalizado)
        self.hsv_button = ttk.Button(info_frame, text="Abrir Sliders HSV", command=self.open_hsv_sliders)
        self.hsv_button.grid(row=0, column=4, rowspan=2, padx=(30, 0))
        self.hsv_button.state(['disabled'])

        # Frame para estatísticas de todos os perfis (apenas para imagem estática)
        self.stats_frame = ttk.LabelFrame(bottom_frame, text="Análise de Vegetação por Perfil", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(10, 0))

        # Criar labels para cada perfil
        self.profile_stats_labels = {}
        for i, profile_name in enumerate(self.profile_names):
            if profile_name != "Personalizado":
                ttk.Label(self.stats_frame, text=f"{profile_name}:", font=('Arial', 10, 'bold')).grid(row=0, column=i*2, sticky=tk.W, padx=(0, 5))
                label = ttk.Label(self.stats_frame, text="0.00%", font=('Arial', 10))
                label.grid(row=0, column=i*2+1, sticky=tk.W, padx=(0, 20))
                self.profile_stats_labels[profile_name] = label

    def on_profile_change(self, event):
        selection = self.profile_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_profile_name = self.profile_names[index]

            # Atualizar labels
            self.profile_label.config(text=self.current_profile_name)
            self.description_label.config(text=self.vegetation_profiles[self.current_profile_name]["descricao"])

            # Habilitar/desabilitar botão HSV
            if self.current_profile_name == "Personalizado":
                self.hsv_button.state(['!disabled'])
            else:
                self.hsv_button.state(['disabled'])
                if self.hsv_sliders_created:
                    cv2.destroyWindow("HSV Sliders")
                    self.hsv_sliders_created = False

            # Se estiver no modo imagem estática, reprocessar
            if not self.use_camera.get() and self.static_image is not None:
                self.process_static_image()

    def on_source_change(self):
        if self.use_camera.get():
            # Mudou para câmera
            self.import_button.state(['disabled'])
            self.static_image = None
            if not self.cap or not self.cap.isOpened():
                self.start_camera()
        else:
            # Mudou para imagem
            self.import_button.state(['!disabled'])
            if self.cap and self.cap.isOpened():
                self.cap.release()
                self.cap = None

    def import_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp"), ("Todos os arquivos", "*.*")]
        )

        if file_path:
            # Carregar imagem
            image = cv2.imread(file_path)
            if image is not None:
                self.static_image = image
                # Redimensionar se necessário
                height, width = image.shape[:2]
                self.new_width, self.new_height = window_size_adjuster(width, height)
                self.static_image = cv2.resize(self.static_image, (self.new_width, self.new_height))
                # Processar imagem imediatamente
                self.process_static_image()

    def open_hsv_sliders(self):
        if not self.hsv_sliders_created:
            cv2.namedWindow("HSV Sliders")
            cv2.createTrackbar("H Min", "HSV Sliders", 0, 179, lambda x: None)
            cv2.createTrackbar("S Min", "HSV Sliders", 0, 255, lambda x: None)
            cv2.createTrackbar("V Min", "HSV Sliders", 0, 255, lambda x: None)
            cv2.createTrackbar("H Max", "HSV Sliders", 179, 179, lambda x: None)
            cv2.createTrackbar("S Max", "HSV Sliders", 255, 255, lambda x: None)
            cv2.createTrackbar("V Max", "HSV Sliders", 255, 255, lambda x: None)
            self.hsv_sliders_created = True

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.new_width, self.new_height = window_size_adjuster(original_width, original_height)

            self.running = True
            self.update_frame()

    def process_static_image(self):
        if self.static_image is not None:
            frame = self.static_image.copy()

            # Converter para HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Calcular porcentagens para todos os perfis
            self.calculate_all_profile_percentages(hsv)

            # Obter valores HSV do perfil atual
            if self.current_profile_name == "Personalizado" and self.hsv_sliders_created:
                h_min = cv2.getTrackbarPos("H Min", "HSV Sliders")
                s_min = cv2.getTrackbarPos("S Min", "HSV Sliders")
                v_min = cv2.getTrackbarPos("V Min", "HSV Sliders")
                h_max = cv2.getTrackbarPos("H Max", "HSV Sliders")
                s_max = cv2.getTrackbarPos("S Max", "HSV Sliders")
                v_max = cv2.getTrackbarPos("V Max", "HSV Sliders")
            else:
                profile = self.vegetation_profiles[self.current_profile_name]
                h_min = profile["h_min"]
                s_min = profile["s_min"]
                v_min = profile["v_min"]
                h_max = profile["h_max"]
                s_max = profile["s_max"]
                v_max = profile["v_max"]

            # Criar filtro
            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv, lower, upper)

            # Aplicar filtro
            result = cv2.bitwise_and(frame, frame, mask=mask)

            # Calcular porcentagem do perfil atual
            total_pixels = mask.size
            pixels_filtrados = cv2.countNonZero(mask)
            porcentagem = round((pixels_filtrados / total_pixels) * 100, 2)

            # Atualizar labels
            self.coverage_label.config(text=f"{porcentagem}%")
            if porcentagem > 30:
                self.status_label.config(text="Densa", foreground="green")
            else:
                self.status_label.config(text="Rasa", foreground="orange")

            # Criar imagem combinada (original + filtrada)
            combined = self.create_combined_image(frame, result, porcentagem)

            # Converter para imagem Tkinter
            combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(combined_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            # Atualizar canvas
            self.canvas.img_tk = img_tk
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    def calculate_all_profile_percentages(self, hsv):
        """Calcula a porcentagem de cada perfil na imagem"""
        total_pixels = hsv.size

        for profile_name in self.profile_names:
            if profile_name != "Personalizado":
                profile = self.vegetation_profiles[profile_name]
                lower = np.array([profile["h_min"], profile["s_min"], profile["v_min"]])
                upper = np.array([profile["h_max"], profile["s_max"], profile["v_max"]])
                mask = cv2.inRange(hsv, lower, upper)
                pixels_filtrados = cv2.countNonZero(mask)
                porcentagem = round((pixels_filtrados / total_pixels) * 100, 2)

                # Atualizar label do perfil
                if profile_name in self.profile_stats_labels:
                    self.profile_stats_labels[profile_name].config(text=f"{porcentagem}%")

    def create_combined_image(self, original, filtered, percentage):
        """Cria imagem combinada com original e filtrada lado a lado"""
        height, width = original.shape[:2]

        # Criar imagem combinada (2x o tamanho da largura)
        combined = np.zeros((height, width * 2, 3), dtype=np.uint8)

        # Colocar imagem original à esquerda
        combined[:, :width] = original

        # Colocar imagem filtrada à direita
        combined[:, width:] = filtered

        # Adicionar linha divisória
        cv2.line(combined, (width, 0), (width, height), (255, 255, 255), 2)

        # Adicionar labels
        # Label "Original"
        cv2.putText(combined, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Label "Filtrado" com porcentagem
        cv2.putText(combined, f"Filtrado: {percentage}%", (width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return combined

    def update_frame(self):
        if self.use_camera.get():
            # Modo câmera
            if self.running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Redimensionar frame
                    frame = cv2.resize(frame, (self.new_width, self.new_height))

                    # Converter para HSV
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                    # Obter valores HSV
                    if self.current_profile_name == "Personalizado" and self.hsv_sliders_created:
                        h_min = cv2.getTrackbarPos("H Min", "HSV Sliders")
                        s_min = cv2.getTrackbarPos("S Min", "HSV Sliders")
                        v_min = cv2.getTrackbarPos("V Min", "HSV Sliders")
                        h_max = cv2.getTrackbarPos("H Max", "HSV Sliders")
                        s_max = cv2.getTrackbarPos("S Max", "HSV Sliders")
                        v_max = cv2.getTrackbarPos("V Max", "HSV Sliders")
                    else:
                        profile = self.vegetation_profiles[self.current_profile_name]
                        h_min = profile["h_min"]
                        s_min = profile["s_min"]
                        v_min = profile["v_min"]
                        h_max = profile["h_max"]
                        s_max = profile["s_max"]
                        v_max = profile["v_max"]

                    # Criar filtro
                    lower = np.array([h_min, s_min, v_min])
                    upper = np.array([h_max, s_max, v_max])
                    mask = cv2.inRange(hsv, lower, upper)

                    # Aplicar filtro
                    result = cv2.bitwise_and(frame, frame, mask=mask)

                    # Calcular porcentagem
                    total_pixels = mask.size
                    pixels_filtrados = cv2.countNonZero(mask)
                    porcentagem = round((pixels_filtrados / total_pixels) * 100, 2)

                    # Atualizar labels
                    self.coverage_label.config(text=f"{porcentagem}%")
                    if porcentagem > 30:
                        self.status_label.config(text="Densa", foreground="green")
                    else:
                        self.status_label.config(text="Rasa", foreground="orange")

                    # Criar imagem combinada (original + filtrada)
                    combined = self.create_combined_image(frame, result, porcentagem)

                    # Converter para imagem Tkinter
                    combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(combined_rgb)
                    img_tk = ImageTk.PhotoImage(image=img_pil)

                    # Atualizar canvas
                    self.canvas.img_tk = img_tk
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

                # Atualizar a cada 30ms
                self.root.after(30, self.update_frame)
        else:
            # Modo imagem estática - reprocessar quando mudar perfil
            if self.static_image is not None:
                self.process_static_image()

    def on_closing(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.hsv_sliders_created:
            cv2.destroyWindow("HSV Sliders")
        cv2.destroyAllWindows()
        self.root.destroy()


# Iniciar aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = VegetationDetectorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
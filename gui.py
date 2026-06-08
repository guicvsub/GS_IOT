"""
Módulo de interface gráfica (GUI) usando Tkinter.
"""
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
from vegetation_profiles import get_vegetation_profiles, get_biome_mapping
from image_processor import (
    window_size_adjuster,
    apply_hsv_filter,
    calculate_coverage_percentage,
    create_combined_image,
    calculate_profile_percentages,
    identify_predominant_vegetation
)


class VegetationDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Detector de Vegetação - GS_IOT")
        self.root.geometry("1200x800")

        # Carregar perfis e biomas
        self.vegetation_profiles = get_vegetation_profiles()
        self.profile_names = list(self.vegetation_profiles.keys())
        self.current_profile_name = self.profile_names[0]
        self.biome_mapping = get_biome_mapping()

        # Variáveis de controle
        self.running = False
        self.cap = None
        self.hsv_sliders_created = False
        self.use_camera = tk.BooleanVar(value=True)
        self.static_image = None

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

        # Frame para bioma predominante (apenas para imagem estática)
        self.biome_frame = ttk.LabelFrame(bottom_frame, text="Bioma Brasileiro Identificado", padding=10)
        self.biome_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(self.biome_frame, text="Bioma:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.biome_label = ttk.Label(self.biome_frame, text="--", font=('Arial', 12))
        self.biome_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 30))

        ttk.Label(self.biome_frame, text="Vegetação Predominante:", font=('Arial', 12, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.predominant_vegetation_label = ttk.Label(self.biome_frame, text="--", font=('Arial', 12))
        self.predominant_vegetation_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 30))

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
            profile_percentages = calculate_profile_percentages(hsv, self.vegetation_profiles)
            predominant_profile, predominant_percentage = identify_predominant_vegetation(profile_percentages)

            # Inferir bioma
            if predominant_profile:
                biome = self.biome_mapping.get(predominant_profile, "Desconhecido")
                self.biome_label.config(text=biome)
                self.predominant_vegetation_label.config(text=f"{predominant_profile} ({predominant_percentage}%)")
            else:
                self.biome_label.config(text="--")
                self.predominant_vegetation_label.config(text="--")

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

            # Aplicar filtro
            result, mask = apply_hsv_filter(frame, h_min, s_min, v_min, h_max, s_max, v_max)

            # Calcular porcentagem do perfil atual
            porcentagem = calculate_coverage_percentage(mask)

            # Atualizar labels
            self.coverage_label.config(text=f"{porcentagem}%")
            if porcentagem > 30:
                self.status_label.config(text="Densa", foreground="green")
            else:
                self.status_label.config(text="Rasa", foreground="orange")

            # Criar imagem combinada (original + filtrada)
            combined = create_combined_image(frame, result, porcentagem)

            # Converter para imagem Tkinter
            combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(combined_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)

            # Atualizar canvas
            self.canvas.img_tk = img_tk
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    def update_frame(self):
        if self.use_camera.get():
            # Modo câmera
            if self.running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Redimensionar frame
                    frame = cv2.resize(frame, (self.new_width, self.new_height))

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

                    # Aplicar filtro
                    result, mask = apply_hsv_filter(frame, h_min, s_min, v_min, h_max, s_max, v_max)

                    # Calcular porcentagem
                    porcentagem = calculate_coverage_percentage(mask)

                    # Atualizar labels
                    self.coverage_label.config(text=f"{porcentagem}%")
                    if porcentagem > 30:
                        self.status_label.config(text="Densa", foreground="green")
                    else:
                        self.status_label.config(text="Rasa", foreground="orange")

                    # Criar imagem combinada (original + filtrada)
                    combined = create_combined_image(frame, result, porcentagem)

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

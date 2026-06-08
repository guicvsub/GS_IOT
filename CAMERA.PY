import cv2
import numpy as np

def nothing(x):
    pass


def window_size_adjuster(width, height):
    if width>1200 or height>700:
        width/=2
        height/=2
        width, height = window_size_adjuster(width, height)
    return round(width), round(height)


def text_constructor(x_coordinates: int,
                     y_coordinate: int,
                     main_text: str,
                     warn_text: str = None,
                     status_ok: bool = False):
    if warn_text:
        if status_ok:
            text_message = main_text
            text_font_color = (0, 123, 0)
        else:
            text_message = warn_text
            text_font_color = (0, 0, 123)
    else:
        text_message = main_text
        text_font_color = (123, 0, 0)
    text_coordinates = (x_coordinates, y_coordinate)
    text_font_family = cv2.FONT_HERSHEY_SIMPLEX
    text_font_size = 1.0
    text_font_weight = 4
    text_line_draw = cv2.LINE_AA ## Anti-aliasing
    return text_message, text_coordinates, text_font_family, text_font_size, text_font_color, text_font_weight, text_line_draw


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


# Abre a webcam
cap = cv2.VideoCapture(0)
original_frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
original_frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
new_frame_width, new_frame_height = window_size_adjuster(original_frame_width, original_frame_height)

# Carregar perfis de vegetação
vegetation_profiles = get_vegetation_profiles()
profile_names = list(vegetation_profiles.keys())

# Cria janela
cv2.namedWindow("HSV Ajuste")

# Criar trackbar para cada perfil (funciona como botão toggle)
profile_trackbars = {}
for i, profile_name in enumerate(profile_names):
    cv2.createTrackbar(profile_name, "HSV Ajuste", 0, 1, nothing)
    profile_trackbars[profile_name] = 0

# Ativar perfil padrão inicialmente
cv2.setTrackbarPos("Padrao", "HSV Ajuste", 1)
profile_trackbars["Padrao"] = 1

# Variáveis para controlar sliders HSV
hsv_sliders_created = False
hsv_window_name = "HSV Sliders"

# Variável para controlar perfil atual
current_profile_name = "Padrao"

while True:
    ret, frame = cap.read()
    if not ret:
        break
    ## Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    ## Verificar mudança de perfil pelos trackbars individuais
    selected_profile = None
    for profile_name in profile_names:
        trackbar_value = cv2.getTrackbarPos(profile_name, "HSV Ajuste")
        if trackbar_value == 1:
            selected_profile = profile_name
            break

    # Se nenhum perfil selecionado, manter o atual
    if selected_profile is None:
        selected_profile = current_profile_name

    # Se mudou de perfil
    if selected_profile != current_profile_name:
        # Desativar o perfil anterior
        cv2.setTrackbarPos(current_profile_name, "HSV Ajuste", 0)
        profile_trackbars[current_profile_name] = 0

        # Ativar o novo perfil
        current_profile_name = selected_profile
        cv2.setTrackbarPos(current_profile_name, "HSV Ajuste", 1)
        profile_trackbars[current_profile_name] = 1

        # Se mudou para Personalizado, criar janela de sliders HSV
        if current_profile_name == "Personalizado":
            if not hsv_sliders_created:
                cv2.namedWindow(hsv_window_name)
                cv2.createTrackbar("H Min", hsv_window_name, 0, 179, nothing)
                cv2.createTrackbar("S Min", hsv_window_name, 0, 255, nothing)
                cv2.createTrackbar("V Min", hsv_window_name, 0, 255, nothing)
                cv2.createTrackbar("H Max", hsv_window_name, 179, 179, nothing)
                cv2.createTrackbar("S Max", hsv_window_name, 255, 255, nothing)
                cv2.createTrackbar("V Max", hsv_window_name, 255, 255, nothing)
                hsv_sliders_created = True
        # Se mudou para outro perfil, destruir janela de sliders HSV
        else:
            if hsv_sliders_created:
                cv2.destroyWindow(hsv_window_name)
                hsv_sliders_created = False

    ## Obter valores HSV baseado no perfil
    if current_profile_name == "Personalizado" and hsv_sliders_created:
        # Ler valores dos sliders
        h_min = cv2.getTrackbarPos("H Min", hsv_window_name)
        s_min = cv2.getTrackbarPos("S Min", hsv_window_name)
        v_min = cv2.getTrackbarPos("V Min", hsv_window_name)
        h_max = cv2.getTrackbarPos("H Max", hsv_window_name)
        s_max = cv2.getTrackbarPos("S Max", hsv_window_name)
        v_max = cv2.getTrackbarPos("V Max", hsv_window_name)
    else:
        # Usar valores do perfil selecionado
        profile = vegetation_profiles[current_profile_name]
        h_min = profile["h_min"]
        s_min = profile["s_min"]
        v_min = profile["v_min"]
        h_max = profile["h_max"]
        s_max = profile["s_max"]
        v_max = profile["v_max"]

    current_profile_desc = vegetation_profiles[current_profile_name]["descricao"]

    ## Criar filtro
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)

    ## Aplicar filtro
    result = cv2.bitwise_and(frame, frame, mask=mask)

    ## Calcular porcentagem da cobertura vegetal
    total_pixels = mask.size
    pixels_filtrados = cv2.countNonZero(mask)
 
    porcentagem_cobertura_vegetal = round((pixels_filtrados / total_pixels) * 100, 2)
    cobertura_vegetal = True if porcentagem_cobertura_vegetal>30 else False

    ## Aplicar Legenda
    result = cv2.rectangle(result, (10, 10), (600, 140), (0,0,0), -1)

    # Mostrar perfil atual
    result = cv2.putText(
        result,
        *text_constructor(
            20,
            30,
            f"Perfil: {current_profile_name}",
            None,
            False))

    # Mostrar descrição do perfil
    result = cv2.putText(
        result,
        *text_constructor(
            20,
            55,
            f"{current_profile_desc}",
            None,
            False))

    # Mostrar porcentagem de cobertura
    result = cv2.putText(
        result,
        *text_constructor(
            20,
            80,
            f">Cobertura Vegetal Densa({porcentagem_cobertura_vegetal}%)",
            f">Cobertura Vegetal Rasa({porcentagem_cobertura_vegetal}%)",
            cobertura_vegetal))

    # Mostra as janelas
    # cv2.imshow("Original", frame)
    # cv2.imshow("Máscara", mask)
    cv2.imshow("Filtrado", result)


    if cv2.waitKey(1) & 0xFF == 27:  # ESC para sair
        break

cap.release()
cv2.destroyAllWindows()
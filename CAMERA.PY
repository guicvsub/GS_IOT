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
    text_font_size = 1.5
    text_font_weight = 4
    text_line_draw = cv2.LINE_AA ## Anti-aliasing
    return text_message, text_coordinates, text_font_family, text_font_size, text_font_color, text_font_weight, text_line_draw


# Abre a webcam
cap = cv2.VideoCapture(0)
original_frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
original_frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
new_frame_width, new_frame_height = window_size_adjuster(original_frame_width, original_frame_height)

# Cria janela e trackbars
cv2.namedWindow("HSV Ajuste")

cv2.createTrackbar("H Min", "HSV Ajuste", 0, 179, nothing)
cv2.createTrackbar("S Min", "HSV Ajuste", 0, 255, nothing)
cv2.createTrackbar("V Min", "HSV Ajuste", 0, 255, nothing)
cv2.createTrackbar("H Max", "HSV Ajuste", 179, 179, nothing)
cv2.createTrackbar("S Max", "HSV Ajuste", 255, 255, nothing)
cv2.createTrackbar("V Max", "HSV Ajuste", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    ## Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    ## Ler valores dos sliders
    h_min = cv2.getTrackbarPos("H Min", "HSV Ajuste")
    s_min = cv2.getTrackbarPos("S Min", "HSV Ajuste")
    v_min = cv2.getTrackbarPos("V Min", "HSV Ajuste")
    h_max = cv2.getTrackbarPos("H Max", "HSV Ajuste")
    s_max = cv2.getTrackbarPos("S Max", "HSV Ajuste")
    v_max = cv2.getTrackbarPos("V Max", "HSV Ajuste")

    ## Criar filtro
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)

    ## Aplicar filtro
    result = cv2.bitwise_and(frame, frame, mask=mask)

    ## Calcular porcentagem da cobertura vegetal
    total_pixels = mask.size
    pixels_filtrados = cv2.countNonZero(mask)
    pixels_nao_afetados = total_pixels - pixels_filtrados
    porcentagem_cobertura_vegetal = round((pixels_nao_afetados / total_pixels) * 100, 2)
    cobertura_vegetal = True if porcentagem_cobertura_vegetal>30 else False

    ## Aplicar Legenda
    result = cv2.rectangle(result, (10, 10), (550, 120), (0,0,0), -1)
    result = cv2.putText(
        result,
        *text_constructor(
            20,
            50,
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
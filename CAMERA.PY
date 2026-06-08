import cv2
import numpy as np
 
def nothing(x):
    pass
 
# Abre a webcam
cap = cv2.VideoCapture(0)
 
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
 
    # Converte para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
 
    # Lê os valores dos sliders
    h_min = cv2.getTrackbarPos("H Min", "HSV Ajuste")
    s_min = cv2.getTrackbarPos("S Min", "HSV Ajuste")
    v_min = cv2.getTrackbarPos("V Min", "HSV Ajuste")
    h_max = cv2.getTrackbarPos("H Max", "HSV Ajuste")
    s_max = cv2.getTrackbarPos("S Max", "HSV Ajuste")
    v_max = cv2.getTrackbarPos("V Max", "HSV Ajuste")
 
    # Cria máscara
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)
 
    # Aplica a máscara
    result = cv2.bitwise_and(frame, frame, mask=mask)
 
    # Mostra as janelas
    cv2.imshow("Original", frame)
    cv2.imshow("Máscara", mask)
    cv2.imshow("Filtrado", result)
 
    if cv2.waitKey(1) & 0xFF == 27:  # ESC para sair
        break
 
cap.release()
cv2.destroyAllWindows()
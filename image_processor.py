"""
Módulo para processamento de imagens e detecção de vegetação.
"""
import cv2
import numpy as np


def window_size_adjuster(width, height):
    """Ajusta o tamanho da janela se for muito grande."""
    if width > 1200 or height > 700:
        width /= 2
        height /= 2
        width, height = window_size_adjuster(width, height)
    return round(width), round(height)


def apply_hsv_filter(image, h_min, s_min, v_min, h_max, s_max, v_max):
    """Aplica filtro HSV na imagem."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result, mask


def calculate_coverage_percentage(mask):
    """Calcula a porcentagem de cobertura vegetal."""
    total_pixels = mask.size
    pixels_filtrados = cv2.countNonZero(mask)
    porcentagem = round((pixels_filtrados / total_pixels) * 100, 2)
    return porcentagem


def create_combined_image(original, filtered, percentage):
    """Cria imagem combinada com original e filtrada lado a lado."""
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
    cv2.putText(combined, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(combined, f"Filtrado: {percentage}%", (width + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    return combined


def calculate_profile_percentages(hsv, profiles):
    """Calcula a porcentagem de cada perfil na imagem."""
    total_pixels = hsv.size
    profile_percentages = {}

    for profile_name, profile in profiles.items():
        if profile_name != "Personalizado":
            lower = np.array([profile["h_min"], profile["s_min"], profile["v_min"]])
            upper = np.array([profile["h_max"], profile["s_max"], profile["v_max"]])
            mask = cv2.inRange(hsv, lower, upper)
            pixels_filtrados = cv2.countNonZero(mask)
            porcentagem = round((pixels_filtrados / total_pixels) * 100, 2)
            profile_percentages[profile_name] = porcentagem

    return profile_percentages


def identify_predominant_vegetation(profile_percentages):
    """Identifica a vegetação predominante baseada nas porcentagens."""
    if not profile_percentages:
        return None, 0.0

    predominant_profile = max(profile_percentages, key=profile_percentages.get)
    predominant_percentage = profile_percentages[predominant_profile]
    return predominant_profile, predominant_percentage

"""
Módulo para gerenciar perfis de vegetação e mapeamento de biomas brasileiros.
"""


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


def get_biome_mapping():
    """
    Mapeia tipos de vegetação para biomas brasileiros.
    """
    biome_mapping = {
        "Padrao": "Cerrado",
        "Verde Escuro": "Floresta Amazônica",
        "Verde Claro": "Pantanal",
        "Amarelado": "Caatinga",
        "Marron": "Mata Atlântica (Seca)"
    }
    return biome_mapping


def apply_profile(profile_name, profiles):
    """
    Aplica os valores do perfil selecionado aos sliders.
    Retorna o dicionário com os valores do perfil.
    """
    if profile_name in profiles:
        return profiles[profile_name]
    return profiles["Padrao"]

"""
Módulo principal do Detector de Vegetação - GS_IOT.
Este módulo conecta o frontend (GUI) com o backend (processamento de imagem).
"""
import tkinter as tk
from gui import VegetationDetectorApp


def main():
    """Função principal para iniciar a aplicação."""
    root = tk.Tk()
    app = VegetationDetectorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

# main.py
# Ponto de entrada da aplicação.

import sys
import os

# Garante que imports funcionem
sys.path.append(os.getcwd())

from src.app.game import Jogo

if __name__ == "__main__":
    # Cria uma instância do jogo
    app = Jogo()
    
    # Inicia o loop principal
    app.executar()

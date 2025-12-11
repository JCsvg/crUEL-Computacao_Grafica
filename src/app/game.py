# src/app/game.py
# Este arquivo contém a lógica principal da janela e o loop do jogo usando Pygame.
# Ele serve como a "ponte" entre o sistema operacional (janela/eventos) e o Planetário (renderização).

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Importa configurações globais e a classe principal da simulação
from src.config import LARGURA_TELA, ALTURA_TELA, TITULO_JANELA, FPS
from src.app.planetario import Planetario

class Jogo:
    """
    Gerencia a janela principal, contexto OpenGL e o loop de eventos (Game Loop).
    """
    def __init__(self):
        # Inicializa subsistemas do Pygame
        pygame.init()
        pygame.font.init() # Inicializa fontes
        
        # Cria a janela com suporte a OpenGL e redimensionamento
        pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption(TITULO_JANELA)
        
        self.clock = pygame.time.Clock()
        self.planetario = Planetario()
        self.running = True
        
        # Estado da tela de ajuda
        self.mostrar_ajuda = True
        self.textura_ajuda = self._criar_textura_ajuda()

    def _criar_textura_ajuda(self):
        """Gera uma textura OpenGL contendo o texto de instruções."""
        font = pygame.font.SysFont("Arial", 20, bold=True)
        texto_linhas = [
            "INSTRUÇÕES DO SISTEMA SOLAR",
            "",
            "Controles de Câmera:",
            "  [Z] / [X] : Zoom In / Zoom Out",
            "  [W, A, S, D] : Orbitar Câmera (Girar ao redor do foco)",
            "  [Setas] : Panning (Mover o ponto de foco pelo espaço)",
            "",
            "Outros:",
            "  [Insert] : Mostrar/Ocultar Linhas de Órbita",
            "  [C] : Segure para Aumentar Velocidade (Turbo)",
            "  [F] : Pausar/Continuar Simulação",
            "  [ESC] : Abrir/Fechar esta tela de ajuda",
        ]
        
        # Renderiza texto em uma Surface Pygame
        # Cor branca, fundo semi-transparente preto
        w, h = 600, 400
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 200)) # Fundo preto semi-transparente
        
        y_offset = 20
        for linha in texto_linhas:
            render = font.render(linha, True, (255, 255, 255))
            x_pos = (w - render.get_width()) // 2
            surface.blit(render, (x_pos, y_offset))
            y_offset += 30
            
        # Borda
        pygame.draw.rect(surface, (255, 255, 255), (0, 0, w, h), 2)
        
        # Converte para textura OpenGL
        data = pygame.image.tostring(surface, "RGBA", 1)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glBindTexture(GL_TEXTURE_2D, 0)
        
        return tex_id

    def _desenhar_ajuda(self, width, height):
        """Desenha o overlay de ajuda na tela."""
        if not self.textura_ajuda: return

        # Salva estados anteriores
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBindTexture(GL_TEXTURE_2D, self.textura_ajuda)
        glColor4f(1, 1, 1, 1)
        
        # Centraliza o quadro de ajuda
        painel_w, painel_h = 600, 400
        x = (width - painel_w) / 2
        y = (height - painel_h) / 2
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + painel_w, y)
        glTexCoord2f(1, 1); glVertex2f(x + painel_w, y + painel_h)
        glTexCoord2f(0, 1); glVertex2f(x, y + painel_h)
        glEnd()
        
        # Restaura estados
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def executar(self):
        """Inicia e mantém o loop principal do programa."""
        while self.running:
            # --- Controle de Tempo ---
            dt = self.clock.tick(FPS)
            w, h = pygame.display.get_surface().get_size()
            
            # --- Processamento de Eventos (Discretos) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    pygame.display.set_mode((event.w, event.h), DOUBLEBUF | OPENGL | RESIZABLE)
                    self.planetario.config_camera_projecao(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_ESCAPE:
                         # Alterna exibição da ajuda
                         self.mostrar_ajuda = not self.mostrar_ajuda
                     else:
                         self.planetario.processar_evento(event)
                else:
                    self.planetario.processar_evento(event)
            
            # --- Input Contínuo e Lógica ---
            if not self.mostrar_ajuda:
                pressed_keys = pygame.key.get_pressed()
                self.planetario.processar_input(pressed_keys)
                
                # Turbo (Tecla C)
                fator = 5.0 if pressed_keys[pygame.K_c] else 1.0
                
                self.planetario.atualizar(fator_velocidade=fator)
            
            # --- Renderização ---
            self.planetario.config_camera_projecao(w, h)
            # --- Renderização ---
            self.planetario.config_camera_projecao(w, h)
            self.planetario.renderizar()
            
            if self.mostrar_ajuda:
                self._desenhar_ajuda(w, h)
            
            pygame.display.flip()
            
        pygame.quit()

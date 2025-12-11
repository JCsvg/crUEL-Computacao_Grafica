from OpenGL.GL import *
from src.formas.forma import Forma2D

class Retangulo(Forma2D):
    """
    Representa um Retângulo 2D desenhado com OpenGL puro.
    Herda de Forma2D.
    """
    def __init__(self, x=0.0, y=0.0, largura=0.7, altura=0.4,
                 r=1.0, g=1.0, b=1.0, a=1.0):
        super().__init__((x, y), (r, g, b, a))
        self.largura = float(largura)
        self.altura  = float(altura)

    def desenhar(self):
        """Desenha o retângulo na posição (self.x, self.y)."""
        # Verifica se precisa de transparência (Alpha < 1)
        # 0.999 é margem de segurança para float
        need_blend = self.a < 0.999
        
        # Verifica se o Blend já estava ligado
        was_blend  = glIsEnabled(GL_BLEND)
        
        if need_blend and not was_blend:
            glEnable(GL_BLEND)
            # Função de mistura padrão para transparência (SrcAlpha, 1-SrcAlpha)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Configura a cor
        self.aplicar_cor()
        
        # Calcula meias dimensões para desenhar a partir do centro
        hw = self.largura * 0.5
        hh = self.altura  * 0.5
        
        # Desenha o quadrado
        glBegin(GL_QUADS)
        glVertex2f(self.x - hw, self.y - hh) # Inferior Esquerdo
        glVertex2f(self.x + hw, self.y - hh) # Inferior Direito
        glVertex2f(self.x + hw, self.y + hh) # Superior Direito
        glVertex2f(self.x - hw, self.y + hh) # Superior Esquerdo
        glEnd()

        # Desabilita blend se nós o habilitamos localmente
        if need_blend and not was_blend:
            glDisable(GL_BLEND)

    def mover(self, x: float, y: float):
        """Atualiza a posição do retângulo."""
        self.x, self.y = float(x), float(y)

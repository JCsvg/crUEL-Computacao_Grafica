from abc import ABC, abstractmethod
from OpenGL.GL import glColor4f

class Forma2D(ABC):
    """
    Classe Abstrata Base para formas 2D em OpenGL.
    Define a interface padrão que todas as formas devem seguir.
    """
    def __init__(self, coord=(0.0, 0.0), cor=(1.0, 1.0, 1.0, 1.0)):
        # Coordenadas X, Y do centro ou ponto base da forma
        self.x, self.y = coord
        # Cor RGBA (Red, Green, Blue, Alpha) com valores de 0.0 a 1.0
        self.r, self.g, self.b, self.a = cor

    def set_cor(self, r: float, g: float, b: float, a: float = 1.0):
        """Define a cor da forma."""
        self.r, self.g, self.b, self.a = r, g, b, a

    def aplicar_cor(self):
        """Aplica a cor atual ao estado do OpenGL (glColor)."""
        glColor4f(self.r, self.g, self.b, self.a)

    @abstractmethod
    def desenhar(self):
        """Método abstrato que deve ser implementado pelas subclasses para realizar o desenho."""
        raise NotImplementedError

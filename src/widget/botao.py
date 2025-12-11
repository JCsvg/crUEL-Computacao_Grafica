# src/widget/botao.py
import pygame
from OpenGL.GL import *
from src.formas.retangulo import Retangulo

class BotaoRetangulo:
    """
    Botão em coordenadas de mundo (glOrtho -1..1).
    - Fundo (fill) com Retangulo (RGBA)
    - Borda (RGBA)
    - Rótulo = texto do botão (pygame.font → textura OpenGL)
      pos_rotulo: "centro" (dentro) ou "acima"
    """

    def __init__(
        self,
        cx: float, cy: float, largura: float, altura: float,
        rotulo: str | None,
        cor_normal_rgba=(0.20, 0.20, 0.25, 1.0),   # cor do botão parado
        cor_sobre_rgba =(0.30, 0.30, 0.35, 1.0),   # cor quando mouse está em cima (hover)
        ao_clicar=None,                             # callback quando clicar
        tamanho_rotulo: int = 28,                   # tamanho da fonte do rótulo
        cor_rotulo_rgba=(1.0, 1.0, 1.0, 1.0),       # cor do rótulo (RGBA 0..1)
        pos_rotulo: str = "centro",                 # "centro" ou "acima"
        margem_rotulo: float = 0.06,                # distância quando pos_rotulo="acima"
        cor_borda_rgba=(1.0, 1.0, 1.0, 1.0),        # cor da borda
        largura_borda_px: float = 1.5,              # espessura da borda
    ):
        # geometria do botão
        self.cx, self.cy = float(cx), float(cy)
        self.largura, self.altura = float(largura), float(altura)

        # rótulo (texto do botão)
        self.rotulo          = rotulo
        self.tamanho_rotulo  = int(tamanho_rotulo)
        self.pos_rotulo      = pos_rotulo
        self.margem_rotulo   = float(margem_rotulo)
        # pygame usa 0..255 → convertemos de 0..1
        self._rotulo_rgba8   = tuple(int(max(0, min(1, c)) * 255) for c in cor_rotulo_rgba)

        # cores
        self.cor_normal_rgba = tuple(cor_normal_rgba)
        self.cor_sobre_rgba  = tuple(cor_sobre_rgba)
        self.cor_borda_rgba  = tuple(cor_borda_rgba)
        self.largura_borda_px = float(largura_borda_px)

        # ação de clique
        self.ao_clicar = ao_clicar

        # estados do mouse
        self._sobre = False
        self._pressionado = False
        self._mouse_abaixo_anterior = False

        # forma de fundo
        self._retangulo = Retangulo(self.cx, self.cy, self.largura, self.altura, *self.cor_normal_rgba)

        # cache do rótulo (textura OpenGL)
        self._chave_rotulo   = None              # (texto, tamanho, rgba8)
        self._tex_rotulo_id  = None
        self._rotulo_w_px    = 0
        self._rotulo_h_px    = 0

    # ---------------- ciclo ----------------

    def atualizar(self, largura_px: int, altura_px: int) -> bool:
        """Atualiza hover/press/release; retorna True se houve clique."""
        mx, my = pygame.mouse.get_pos()
        bot_esq = pygame.mouse.get_pressed(3)[0]
        x_mundo, y_mundo = self._px_para_mundo(mx, my, largura_px, altura_px)

        dentro = self._colide_mundo(x_mundo, y_mundo)
        self._sobre = dentro

        clicou = False
        # início do clique
        if dentro and bot_esq and not self._mouse_abaixo_anterior:
            self._pressionado = True
        # fim do clique (soltou dentro)
        if self._pressionado and (not bot_esq) and self._mouse_abaixo_anterior:
            if dentro:
                clicou = True
                if callable(self.ao_clicar):
                    self.ao_clicar()
            self._pressionado = False

        self._mouse_abaixo_anterior = bot_esq
        return clicou

    def desenhar(self, largura_px: int, altura_px: int):
        """Desenha fundo, borda e rótulo."""
        # 1) fundo (muda cor com hover)
        cor = self.cor_sobre_rgba if self._sobre else self.cor_normal_rgba
        self._retangulo.r, self._retangulo.g, self._retangulo.b, self._retangulo.a = cor
        self._retangulo.desenhar()

        # 2) borda
        self._desenhar_borda()

        # 3) rótulo (se existir)
        if self.rotulo:
            self._garantir_textura_rotulo()
            self._desenhar_rotulo(largura_px, altura_px)

    # ---------------- privados ----------------

    @staticmethod
    def _px_para_mundo(mx_px: int, my_px: int, w_px: int, h_px: int):
        """Converte pixels → mundo (-1..1)."""
        xw = (mx_px / float(max(1, w_px))) * 2.0 - 1.0
        yw = 1.0 - (my_px / float(max(1, h_px))) * 2.0
        return xw, yw

    def _colide_mundo(self, xw: float, yw: float) -> bool:
        """Teste de ponto dentro do retângulo do botão."""
        meia_l, meia_a = self.largura * 0.5, self.altura * 0.5
        return (self.cx - meia_l <= xw <= self.cx + meia_l) and (self.cy - meia_a <= yw <= self.cy + meia_a)

    def _desenhar_borda(self):
        """Desenha a linha da borda do botão."""
        meia_l, meia_a = self.largura * 0.5, self.altura * 0.5
        x0, y0 = self.cx - meia_l, self.cy - meia_a
        x1, y1 = self.cx + meia_l, self.cy + meia_a

        precisa_blend = self.cor_borda_rgba[3] < 0.999
        blend_antes   = glIsEnabled(GL_BLEND)
        if precisa_blend and not blend_antes:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glLineWidth(self.largura_borda_px)
        glColor4f(*self.cor_borda_rgba)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x0, y0); glVertex2f(x1, y0); glVertex2f(x1, y1); glVertex2f(x0, y1)
        glEnd()

        if precisa_blend and not blend_antes:
            glDisable(GL_BLEND)

    def _garantir_textura_rotulo(self):
        """(Re)gera a textura do rótulo se algo mudou."""
        chave = (self.rotulo, self.tamanho_rotulo, self._rotulo_rgba8)
        if chave == self._chave_rotulo and self._tex_rotulo_id:
            return

        pygame.font.init()
        fonte = pygame.font.Font(None, self.tamanho_rotulo)
        surf  = fonte.render(self.rotulo or "", True, self._rotulo_rgba8).convert_alpha()
        w_px, h_px = surf.get_size()

        # flip=True para casar com texcoords padrão (v=0 em baixo, v=1 em cima)
        dados = pygame.image.tostring(surf, "RGBA", True)

        if not self._tex_rotulo_id:
            self._tex_rotulo_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self._tex_rotulo_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w_px, h_px, 0, GL_RGBA, GL_UNSIGNED_BYTE, dados)
        glBindTexture(GL_TEXTURE_2D, 0)

        self._chave_rotulo  = chave
        self._rotulo_w_px   = w_px
        self._rotulo_h_px   = h_px

    def _centro_do_rotulo(self, largura_px: int, altura_px: int):
        """Calcula centro do rótulo e tamanho em 'mundo'."""
        sx = 2.0 / max(1, largura_px)   # px → mundo (x)
        sy = 2.0 / max(1, altura_px)    # px → mundo (y)
        w, h = self._rotulo_w_px * sx, self._rotulo_h_px * sy

        if self.pos_rotulo == "acima":
            meia_a = self.altura * 0.5
            cx = self.cx
            cy = self.cy + meia_a + self.margem_rotulo + (h * 0.5)
        else:  # "centro"
            cx = self.cx
            cy = self.cy

        return cx, cy, w, h

    def _desenhar_rotulo(self, largura_px: int, altura_px: int):
        """Desenha a textura do rótulo (texto)."""
        if not self._tex_rotulo_id or self._rotulo_w_px == 0 or self._rotulo_h_px == 0:
            return

        cx, cy, w, h = self._centro_do_rotulo(largura_px, altura_px)
        x0, x1 = cx - w * 0.5, cx + w * 0.5
        y0, y1 = cy - h * 0.5, cy + h * 0.5

        depth_antes = glIsEnabled(GL_DEPTH_TEST)
        if depth_antes:
            glDisable(GL_DEPTH_TEST)  # evita briga com o fill

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, self._tex_rotulo_id)
        glColor4f(1, 1, 1, 1)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x0, y0)
        glTexCoord2f(1, 0); glVertex2f(x1, y0)
        glTexCoord2f(1, 1); glVertex2f(x1, y1)
        glTexCoord2f(0, 1); glVertex2f(x0, y1)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        if depth_antes:
            glEnable(GL_DEPTH_TEST)

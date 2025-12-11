# src/formas/primitivas.py
# Biblioteca auxiliar para renderização de formas geométricas via OpenGL/GLU.

from OpenGL.GL import *
from OpenGL.GLU import *
try:
    from OpenGL.GLUT import *
except ImportError:
    pass # GLUT serve aqui apenas para compatibilidade se necessário, mas usamos GLU para esferas.

def desenhar_esfera(raio, textura_id=None, slices=50, stacks=50):
    """
    Renderiza uma esfera sólida ou texturizada.
    """
    # Cria um novo objeto quádrico (estrutura para desenhar formas como esferas, cilindros)
    quad = gluNewQuadric()
    
    if textura_id:
        # Habilita aplicação de textura no quádrico
        gluQuadricTexture(quad, GL_TRUE)
        # Habilita o estado de textura 2D do OpenGL
        glEnable(GL_TEXTURE_2D)
        # Vincula a textura específica que queremos usar
        glBindTexture(GL_TEXTURE_2D, textura_id)
    else:
        # Se não houver textura, desabilita para garantir que não aplique uma textura residual
        glDisable(GL_TEXTURE_2D)
        
    # Desenha a esfera com o raio e detalhamento especificados
    # A esfera é desenhada centrada na origem atual (0,0,0)
    gluSphere(quad, raio, slices, stacks)
    
    # Libera a memória do objeto quádrico
    gluDeleteQuadric(quad)
    
    if textura_id:
        # Limpa o estado de texturização após o desenho
        glDisable(GL_TEXTURE_2D)

def desenhar_anel(raio_interno, raio_externo, textura_id=None, slices=50, loops=1):
    """
    Desenha um anel (disco com furo central) no plano XZ (horizontal).
    
    Parâmetros:
    - raio_interno: Raio do buraco central.
    - raio_externo: Raio total do disco.
    - textura_id: ID da textura (opcional).
    """
    quad = gluNewQuadric()
    
    if textura_id:
        gluQuadricTexture(quad, GL_TRUE)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, textura_id)
    else:
        glDisable(GL_TEXTURE_2D)
        
    # Salva a matriz atual para não afetar transformações futuras
    glPushMatrix()
    
    # Rotação de 90 graus no eixo X.
    # O gluDisk desenha nativamente no plano XY (vertical).
    # Esta rotação "deita" o anel para que fique alinhado com o plano orbital (XZ).
    glRotatef(90.0, 1.0, 0.0, 0.0)
    
    # Desenha o disco/anel
    gluDisk(quad, raio_interno, raio_externo, slices, loops)
    
    # Restaura a matriz
    glPopMatrix()
    
    gluDeleteQuadric(quad)

    if textura_id:
        glDisable(GL_TEXTURE_2D)

def desenhar_fundo_quad(textura_id):
    """
    Desenha um retângulo (quad) que preenche toda a tela para servir de fundo espacial.
    Usa projeção Ortogonal (2D) para garantir que cubra a tela independentemente da câmera 3D.
    
    Parâmetros:
    - textura_id: Textura do fundo estrelado.
    """
    if not textura_id:
        return

    # 1. Configurar Projeção 2D (Ortho)
    # Mudamos para a matriz de projeção para definir como a cena é achatada na tela
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()       # Salva a projeção 3D atual (Perspectiva)
    glLoadIdentity()     # Reseta
    gluOrtho2D(0, 1, 0, 1) # Define sistema de coordenadas 2D de 0 a 1 em ambos eixos
    
    # 2. Configurar ModelView
    # Mudamos para matriz de modelo para desenhar o objeto
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()       # Salva posição da câmera 3D
    glLoadIdentity()     # Reseta para origem
    
    # 3. Preparar estados do OpenGL para desenho 2D sem iluminação
    glDisable(GL_DEPTH_TEST) # Desliga teste de profundidade (fundo fica sempre atrás)
    glDisable(GL_LIGHTING)   # Desliga luzes (fundo tem emissão própria/é uma imagem)
    glEnable(GL_TEXTURE_2D)  # Liga textura
    glBindTexture(GL_TEXTURE_2D, textura_id)
    
    # Garante que a textura seja desenhada com suas cores originais
    # GL_REPLACE ignora a cor do vértice e usa apenas a cor da textura
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    
    glColor3f(1.0, 1.0, 1.0) # Cor base branca (necessária para alguns modos de env)
    
    # 4. Desenhar o Quadrado cobrindo a tela (0,0 a 1,1)
    glBegin(GL_QUADS)
    # Mapeia coordenadas da Textura (glTexCoord) para coordenadas da Tela (glVertex)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0) # Canto inferior esquerdo
    glTexCoord2f(1.0, 0.0); glVertex2f(1.0, 0.0) # Canto inferior direito
    glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0) # Canto superior direito
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, 1.0) # Canto superior esquerdo
    glEnd()
    
    # Restaura o modo de textura padrão (modulate) para não afetar outros objetos 3D
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    
    # 5. Restaurar estados anteriores
    glEnable(GL_LIGHTING)    # Religa luz
    glEnable(GL_DEPTH_TEST)  # Religa profundidade
    
    glPopMatrix()            # Restaura ModelView
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()            # Restaura Projeção (Perspectiva)
    glMatrixMode(GL_MODELVIEW) # Volta ao modo padrão

def desenhar_esfera_interna(raio, textura_id=None, slices=50, stacks=50):
    """
    Renderiza uma esfera visível por dentro (SkyDome).
    """
    quad = gluNewQuadric()
    
    # Inverte normais para apontar para dentro (iluminação correta se houvesse)
    # E faz o mapeamento de textura ser visível por dentro
    gluQuadricOrientation(quad, GLU_INSIDE)
    
    if textura_id:
        gluQuadricTexture(quad, GL_TRUE)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, textura_id)
    else:
        glDisable(GL_TEXTURE_2D)
        
    gluSphere(quad, raio, slices, stacks)
    
    gluDeleteQuadric(quad)
    
    if textura_id:
        glDisable(GL_TEXTURE_2D)

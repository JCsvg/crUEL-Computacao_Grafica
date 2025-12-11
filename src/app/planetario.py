# src/app/planetario.py
import pygame
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from src.formas.primitivas import desenhar_esfera, desenhar_anel, desenhar_fundo_quad, desenhar_esfera_interna

class Planetario:
    """
    Controla toda a lógica da simulação do Sistema Solar, incluindo renderização,
    carregamento de assets e cálculo de órbitas.
    """
    def __init__(self):
        # Rotação e translação dos planetas
        self.angle = 0.0
        self.rotation = 0.0
        
        # Câmera Híbrida (Órbita + Pan)
        self.cam_dist = 60.0
        self.cam_theta = 1.57   # 90 graus
        self.cam_phi = 1.0      # Elevação
        
        # Ponto focal da câmera
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_z = 0.0
        
        self.mostrar_orbitas = True
        self.paused = False
        
        # --- Gerenciamento de Texturas ---
        # Dicionário para armazenar IDs das texturas OpenGL geradas
        self.texture_ids = {
            'fundo': None, 'sun': None, 'mercury': None, 'venus': None,
            'earth': None, 'moon': None, 'mars': None, 'jupiter': None, 'saturn': None,
            'uranus': None, 'neptune': None, 'satRing': None
        }
        
        # --- Inicialização ---
        self._init_opengl()       # Configura luzes, profundidade, etc.
        self._carregar_texturas() # Carrega imagens do disco para memória de vídeo
        
    def _init_opengl(self):
        """Configurações iniciais do OpenGL."""
        glClearColor(0.0, 0.0, 0.0, 0.0)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_TEXTURE_2D)

    def _carregar_texturas(self):
        """Carrega imagens jpg e cria texturas OpenGL."""
        # Mapeia chaves internas para nomes de arquivos
        files = {
            'fundo': "space.jpg",
            'sun': "sun.jpg",
            'mercury': "mercury.jpg",
            'venus': "venus.jpg",
            'earth': "earth.jpg",
            'moon': "moon.jpg",
            'mars': "mars.png",
            'jupiter': "jupiter.jpg",
            'saturn': "saturn.jpg",
            'uranus': "uranus.jpg",
            'neptune': "neptune.jpg",
            'satRing': "saturnRing.jpg"
        }
        
        base_path = "src/assets/textures/"
        
        for key, filename in files.items():
            try:
                # Carrega imagem usando Pygame
                surface = pygame.image.load(base_path + filename)
                
                # IMPORTANTE: Converte para formato eficiente e garante profundidade de cor correta
                # Isso ajuda a evitar problemas de cores corrompidas ou Grayscale se a imagem for indexada.
                surface = surface.convert()
                
                width = surface.get_width()
                height = surface.get_height()
                
                # Converte os dados da imagem para string de bytes para o OpenGL ler
                # "RGB" indica formato de cor. '1' inverte verticalmente (padrão OpenGL onde Y cresce pra cima)
                data = pygame.image.tostring(surface, "RGB", 1)
                
                # Gera um ID de textura no OpenGL
                tex_id = glGenTextures(1)
                
                # Vincula (seleciona) essa textura para operar nela
                glBindTexture(GL_TEXTURE_2D, tex_id)
                
                # Configura parâmetros de repetição e filtro
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT) # Repete horizontalmente
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT) # Repete verticalmente
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR) # Filtro linear ao reduzir (suave)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # Filtro linear ao ampliar (suave)
                
                # IMPORTANTE: Corrige alinhamento de bytes para larguras não múltiplas de 4
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                
                # Envia os dados de pixels para a GPU
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
                
                # Armazena ID
                self.texture_ids[key] = tex_id
                
            except Exception as e:
                print(f"Erro crítico ao carregar textura {filename}: {e}")

    def atualizar(self, fator_velocidade=1.0):
        """Atualização de lógica a cada frame (Animação)."""
        # Se estiver pausado, não atualiza os ângulos
        if self.paused:
            return

        # Incrementa ângulos para criar movimento de rotação e translação
        self.angle += 0.5 * fator_velocidade   # Velocidade orbital (translação global)
        self.rotation += 1.0 * fator_velocidade # Velocidade rotacional (giro do planeta)

    def processar_input(self, pressed_keys):
        """
        Input contínuo (movimento e zoom).
        """
        
        # --- 1. Zoom (Teclas Z e X) ---
        # Altera o raio da órbita da câmera (`cam_dist`)
        zoom_speed = 1.0
        if pressed_keys[pygame.K_z]:
            self.cam_dist -= zoom_speed # Aproxima
            if self.cam_dist < 5.0: self.cam_dist = 5.0 # Limite mínimo
            
        if pressed_keys[pygame.K_x]:
            self.cam_dist += zoom_speed # Afasta
            if self.cam_dist > 300.0: self.cam_dist = 300.0 # Limite máximo
            
        # --- 2. Rotação Orbital (Teclas WASD) ---
        # Gira a câmera em torno do ponto de foco (Target)
        angle_speed = 0.03
        
        # A / D: Gira horizontalmente (Theta)
        if pressed_keys[pygame.K_a]:
            self.cam_theta -= angle_speed 
        if pressed_keys[pygame.K_d]:
            self.cam_theta += angle_speed 
            
        # W / S: Gira verticalmente (Phi - Elevação)
        if pressed_keys[pygame.K_w]:
            self.cam_phi -= angle_speed   # Sobe
            if self.cam_phi < 0.1: self.cam_phi = 0.1 # Trava para não inverter no polo norte
        if pressed_keys[pygame.K_s]:
            self.cam_phi += angle_speed   # Desce
            if self.cam_phi > 3.1: self.cam_phi = 3.1 # Trava para não inverter no polo sul
            
        # --- 3. Panning / Movimento Livre (Setas) ---
        # Move o Ponto de Foco (`target`) pelo espaço, arrastando a câmera junto.
        # Permite explorar o sistema solar além do centro.
        pan_speed = 0.5
        
        # Calcula vetores de direção baseados no ângulo da câmera para mover "para frente/lados" relativo à visão
        # Vetor View (Projetado no chão XZ)
        dir_x = -math.cos(self.cam_theta)
        dir_z = -math.sin(self.cam_theta)
        
        # Vetor Right (Perpendicular à visão) - Strafe
        # Rotacionado 90 graus
        st_x = math.sin(self.cam_theta)
        st_z = -math.cos(self.cam_theta)
        
        # Cima/Baixo (Setas): Move na direção da visão
        if pressed_keys[pygame.K_UP]: 
            self.target_x += dir_x * pan_speed
            self.target_z += dir_z * pan_speed
        if pressed_keys[pygame.K_DOWN]:
            self.target_x -= dir_x * pan_speed
            self.target_z -= dir_z * pan_speed
            
        # Esquerda/Direita (Setas): Move lateralmente (Strafe)
        if pressed_keys[pygame.K_LEFT]:
            self.target_x -= st_x * pan_speed
            self.target_z -= st_z * pan_speed
        if pressed_keys[pygame.K_RIGHT]:
             self.target_x += st_x * pan_speed
             self.target_z += st_z * pan_speed

    def processar_evento(self, event):
        """Processa eventos discretos (clique único)."""
        if event.type == pygame.KEYDOWN:
            # INSERT alterna a visibilidade das linhas de órbita
            # INSERT alterna a visibilidade das linhas de órbita
            if event.key == pygame.K_INSERT:
                self.mostrar_orbitas = not self.mostrar_orbitas
            
            # F pausa/despausa a simulação
            elif event.key == pygame.K_f:
                self.paused = not self.paused

    def config_camera_projecao(self, width, height):
        """Configura a matriz de projeção e a posição da câmera (ModelView)."""
        if height == 0: height = 1
        
        # Define a área de desenho na janela (Viewport)
        glViewport(0, 0, width, height)
        
        # --- Matriz de Projeção (Lente da câmera) ---
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Define projeção perspectiva (3D realista)
        # fovy=45 graus, aspect=tela, near=1.0, far=1000.0 (Aumentado para evitar corte do fundo)
        gluPerspective(45.0, width / height, 1.0, 1000.0) 
        
        # --- Matriz de Modelo/Visão (Posição da câmera) ---
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Converte Coordenadas Esféricas (Distancia, Theta, Phi) -> Cartesianas (x,y,z)
        # para determinar onde o olho da câmera está.
        # x = r * sin(phi) * cos(theta)
        # z = r * sin(phi) * sin(theta)
        # y = r * cos(phi)
        
        ox = self.cam_dist * math.sin(self.cam_phi) * math.cos(self.cam_theta)
        oz = self.cam_dist * math.sin(self.cam_phi) * math.sin(self.cam_theta)
        oy = self.cam_dist * math.cos(self.cam_phi)
        
        # Posição final da câmera = Posição do Alvo + Offset calculado
        eyeX = self.target_x + ox
        eyeY = self.target_y + oy
        eyeZ = self.target_z + oz
        
        # gluLookAt define a posição e para onde a câmera olha
        gluLookAt(eyeX, eyeY, eyeZ,                    
                  self.target_x, self.target_y, self.target_z, 
                  0.0, 1.0, 0.0)                           

    def renderizar(self):
        """Desenha toda a cena 3D."""
        # Limpa o buffer de cor e o buffer de profundidade antes de desenhar novo quadro
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # --- 1. Desenha Background (Sky Sphere) ---
        # Desenha uma grande esfera ao redor da cena para simular o espaço 3D (não mais "reto")
        
        glDisable(GL_LIGHTING)      # O fundo deve ter brilho próprio (textura), não ser afetado por luzes
        glDepthMask(GL_FALSE)       # Não escreve no Z-Buffer (fundo fica sempre atrás)
        
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)     # Ajusta orientação da textura do espaço
        desenhar_esfera_interna(350.0, self.texture_ids['fundo'])
        glPopMatrix()
        
        glDepthMask(GL_TRUE)        # Volta a escrever no Z-Buffer
        glEnable(GL_LIGHTING)       # Re-habilita iluminação para os planetas
        
        # --- 2. Iluminação do SOL ---
        # Configura a luz para desenhar o Sol. 
        light_pos = [0.0, 0.0, 0.0, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        
        # Sol aceso (Ambiente alto)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [1.0, 1.0, 1.0, 1.0])
        # Difusa alta para iluminar planetas
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.5, 1.5, 1.5, 1.0])

        # Desenha o SOL
        glPushMatrix()
        # Material brilhante
        mat_specular = [1.0, 1.0, 1.0, 1.0]
        mat_shininess = [50.0]
        glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)
        # Emissão
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.3, 0.3, 0.3, 1.0]) 
        
        glPushMatrix()
        glRotatef(self.angle * 0.9, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(5.0, self.texture_ids['sun'])
        glPopMatrix()
        
        # Desliga Emissão
        glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        glPopMatrix()
        
        # --- 3. Iluminação dos PLANETAS ---
        # Modo Solar Fixo: Ambiente baixo (sombra nos lados opostos ao sol)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.05, 0.05, 0.05, 1.0])
        
        # --- 4. Desenho dos Corpos Celestes ---
        # O sistema usa transformações hierárquicas (Pilha de Matrizes - Push/Pop)
        # Ordem: Translação Base -> Rotação Base -> Desenha ou (Nova Push -> Translação lua...)
        
        # OBSERVAÇÃO CRÍTICA DO ERRO ANTERIOR: 
        # O código original tinha um glPushMatrix() ENVOLVENDO TODO O SISTEMA SOLAR (Sol + Planetas).
        # Ao editar o desenho do Sol, eu removi esse Push inicial "acidentalmente" ou o `replace` comeu ele, 
        # mas mantive o `glPopMatrix()` no final do arquivo (linha 432).
        # Vamos reinsirir o Push Mestre aqui para garantir que o Pop final tenha par.
        glPushMatrix() 
        
        # --- MERCÚRIO ---
        glPushMatrix()
        glRotatef(self.angle * 4.15, 0.0, 1.0, 0.0) # Órbita rápida
        glTranslatef(6.0, 0.0, 0.0)                 # Distância do Sol
        glPushMatrix()
        glRotatef(self.rotation * 50, 0.0, 1.0, 0.0) # Rotação própria
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(0.38, self.texture_ids['mercury'])
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(6.0, 6.08, None)
        
        # --- VÊNUS ---
        glPushMatrix()
        glRotatef(self.angle * 1.62, 0.0, 1.0, 0.0)
        glTranslatef(8.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.rotation * -0.9, 0.0, 1.0, 0.0) # Rotação retrógrada
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(0.85, self.texture_ids['venus'])
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(8.0, 8.08, None)
        
        # --- TERRA ---
        glPushMatrix()
        glRotatef(self.angle, 0.0, 1.0, 0.0) # Órbita padrão (referência 1.0)
        glTranslatef(10.0, 0.0, 0.0)
        # Desenha Terra
        glPushMatrix()
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(1.0, self.texture_ids['earth'])
        glPopMatrix()
        
        # --- LUA (Filha da Terra) ---
        # Continua na matriz da Terra (já transladada para 10.0), então translação é local
        glPushMatrix()
        glRotatef(self.rotation, 0.0, 1.0, 0.0) # Rotação da Lua ao redor da Terra
        glTranslatef(1.5, 0.0, 0.0)             # Distância Lua-Terra
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(0.3, self.texture_ids['moon'])
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(1.5, 1.55, None)
        
        glPopMatrix() # Fim do escopo da Terra
        if self.mostrar_orbitas: desenhar_anel(10.0, 10.08, None) # Órbita da Terra
        
        # --- MARTE ---
        glPushMatrix()
        glRotatef(self.angle * 0.53, 0.0, 1.0, 0.0)
        glTranslatef(13.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.rotation * 3, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(0.53, self.texture_ids['mars'])
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(13.0, 13.08, None)
        
        # --- JÚPITER ---
        glPushMatrix()
        glRotatef(self.angle * 0.3, 0.0, 1.0, 0.0)
        glTranslatef(17.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.angle * 7, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(1.85, self.texture_ids['jupiter'])
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(17.0, 17.08, None)
        
        # --- SATURNO ---
        glPushMatrix()
        glRotatef(self.angle * 0.2, 0.0, 1.0, 0.0)
        glTranslatef(23.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.angle * 7, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(1.55, self.texture_ids['saturn'])
        glPopMatrix()
        
        # Anéis de Saturno
        glPushMatrix()
        # Textura específica para anéis
        desenhar_anel(2.0, 2.5, self.texture_ids['satRing'])
        glPopMatrix()
        
        glPopMatrix() # Fim Saturno
        if self.mostrar_orbitas: desenhar_anel(23.0, 23.08, None)
        
        # --- URANO ---
        glPushMatrix()
        glRotatef(self.angle * 0.16, 0.0, 1.0, 0.0)
        glTranslatef(27.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.angle * 12, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(1.2, self.texture_ids['uranus'])
        # Anéis removidos conforme solicitação visual
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(27.0, 27.08, None)
        
        # --- NETUNO ---
        glPushMatrix()
        glRotatef(self.angle * 0.1, 0.0, 1.0, 0.0)
        glTranslatef(33.0, 0.0, 0.0)
        glPushMatrix()
        glRotatef(self.angle * 6, 0.0, 1.0, 0.0)
        glRotatef(-90, 1.0, 0.0, 0.0)
        desenhar_esfera(1.38, self.texture_ids['neptune'])
        glPopMatrix()
        glPopMatrix()
        if self.mostrar_orbitas: desenhar_anel(33.0, 33.08, None)
        
        glPopMatrix() # Finaliza matrix principal (do Sol)

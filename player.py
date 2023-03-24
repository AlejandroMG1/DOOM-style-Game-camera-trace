from img_procesing import normalize, get_lab_segment, get_centroid
from settings import *
import pygame as pg
import math
import cv2


class Player:
    # Variable que guarda la instancia de la captura de video
    camera = None
    # Variable que guarda la posición actual del objeto al que se le hace seguimiento en X
    camera_x_pos = -1

    def __init__(self, game, cam):
        self.camera = cam
        self.game = game
        self.x, self.y = PLAYER_POS
        # variable que controla la camara del jugador
        self.angle = PLAYER_ANGLE
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        # Variable que guarda el recorrido de la camara desde la lectura anterior
        self.rel = 0
        self.health_recovery_delay = 700
        self.time_prev = pg.time.get_ticks()
        # diagonal movement correction
        self.diag_move_corr = 1 / math.sqrt(2)

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over()
            pg.display.flip()
            pg.time.delay(1500)
            self.game.new_game()

    def get_damage(self, damage):
        self.health -= damage
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def single_fire_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.game.sound.shotgun.play()
                self.shot = True
                self.game.weapon.reloading = True

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        num_key_pressed = -1
        if keys[pg.K_w]:
            num_key_pressed += 1
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            num_key_pressed += 1
            dx += -speed_cos
            dy += -speed_sin
        if keys[pg.K_a]:
            num_key_pressed += 1
            dx += speed_sin
            dy += -speed_cos
        if keys[pg.K_d]:
            num_key_pressed += 1
            dx += -speed_sin
            dy += speed_cos

        # diag move correction
        if num_key_pressed:
            dx *= self.diag_move_corr
            dy *= self.diag_move_corr

        self.check_wall_collision(dx, dy)

        # if keys[pg.K_LEFT]:
        #     self.angle -= PLAYER_ROT_SPEED * self.game.delta_time
        # if keys[pg.K_RIGHT]:
        #     self.angle += PLAYER_ROT_SPEED * self.game.delta_time
        self.angle %= math.tau

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def draw(self):
        pg.draw.line(self.game.screen, 'yellow', (self.x * 100, self.y * 100),
                     (self.x * 100 + WIDTH * math.cos(self.angle),
                      self.y * 100 + WIDTH * math.sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, 'green', (self.x * 100, self.y * 100), 15)

    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    """Metodo para controlar la camara del personaje con la camara del equipo"""

    def cam_control(self):
        # Tomo una imagen de la camara
        ret_val, img = self.camera.read()
        # verifico que exista una imagen ya que hay frames donde no se alcanza a tomar una imagen
        if img is not None:
            # normalizo la imagen
            img = normalize(img)
            # Volteo entorno al eje vertical la imagen para que la imagen captada coincida con la tirrección en a la que
            # se encuentra la luz
            img = cv2.flip(img, 1)
            # Tranformo el espacio de color de la imagen a lAB y le asigno el rango de valores que deseo captar
            binar_segment = get_lab_segment(img, (226, 124, 127), (255, 135, 141))

            # si se encuentra al menos un pixel que coincida con el rango definido inicio el proceso de rastreo
            if binar_segment.sum() > 0:
                # obtengo los puntos X y Y del centro del objeto identificado
                c_x, c_y = get_centroid(binar_segment)
                # marco un indicador en el centro del objeto identificado
                cv2.circle(img, (c_x, c_y), 3, (0, 255, 0), -1)
                # si es la primera vez que se identifica un objeto al cual hacer seguimiento se asigna el valor del
                # centro en X como posición inicial
                if self.camera_x_pos == -1:
                    self.camera_x_pos = c_x
                # de lo contrario se procede a hacer el movimiento de la camara del personaje
                else:
                    # primero guardo el recorrido del objeto en la imagen desde la anterior captura
                    self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, c_x - self.camera_x_pos))
                    # actualizo la camara del personaje teniendo en cuenta el recorrido del objeto, un valor de
                    # sensibilidad, el ancho de la camara y la diferencia de tiempo
                    self.angle += self.rel * CAMERA_SENSITIVITY * img.shape[1] * self.game.delta_time
                    # actualizo la posición actual del objeto
                    self.camera_x_pos = c_x

            cv2.imshow('webcam', img)

            if cv2.waitKey(1) == 27:
                self.camera.release()

    def update(self):
        self.movement()
        self.mouse_control()
        # introdusco el control por la camara del equipo en el flujo del juego
        self.cam_control()
        self.recover_health()

    @property
    def pos(self):
        return self.x, self.y

    @property
    def map_pos(self):
        return int(self.x), int(self.y)

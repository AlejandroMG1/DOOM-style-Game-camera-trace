import numpy as np
import cv2
import skimage


"""Metodo que recibe una imagen y la normaliza con valores entre 0 y 255"""


def normalize(a):
    a = a.astype(np.double)
    a = a / a.max() * 255
    b = a.astype(np.uint8)
    return b


"""Metodo que recibe una imagen e identifica los colores que esten entre el rango minimo y maximo dados en el espacio lab"""


def get_lab_segment(img, min, max):
    # Convierto la imagen a LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    # realizo la umbralización de la imagen con el rango definido
    a_binar = cv2.inRange(lab, min, max)
    # creo los elemtos estructurales para realizar eroción y dilatación respectivamente
    kernel = np.ones((4, 4), np.uint8)
    kernel_d = skimage.morphology.disk(3)

    # erociono la imagen para remover pixeles sueltos que hallan podido coicidir con el rango dado
    a_binar = cv2.erode(a_binar, kernel)
    # Dilato para rellenar y redondear el objeto remanente
    a_binar = cv2.dilate(a_binar, kernel_d)
    return a_binar

"""Metodo que calcula el centride de un objeto unico en la imagen"""
def get_centroid(bin_img):
    # Calculo los momentos del blob
    M = cv2.moments(bin_img)

    # calculo las coordenadas en X y Y del centroide del blob
    c_x = int(M["m10"] / M["m00"])
    c_y = int(M["m01"] / M["m00"])
    return c_x, c_y

import pygame
import cv2
import numpy as np
import sys
import time
import io
import os
import threading

# set up the camera
time.sleep(1)
camera = cv2.VideoCapture(0)
camera.set(3, 640) #WIDTH
camera.set(4, 480) #HEIGHT
# set up a video stream
face_cascade = cv2.CascadeClassifier("data/haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("data/haarcascade_eye.xml")
# set up pygame, the library for displaying images
pygame.init()
pygame.display.set_caption("OpenCV camera stream on Pygame")
# sets up window dimensions based on camera resolution
screen = pygame.display.set_mode([1200,800])
# variables for drawing onto the screen
screen_width = 1200
screen_height = 800
top_margin = 25
left_margin = 25
font_size = 25
font = pygame.font.Font('data/MODES.ttf', font_size)

total_seconds = 15.0

class States:
    RETR,EXTE,STOP = range(3)
faceLen = 0
def updateMotors():
    global faceLen
    global seconds
    global acState

    acState = States.RETR
    pState = States.RETR
    seconds = 0
    lastSec = time.time()
    while True:
        if faceLen > 0:
            acState = States.STOP
        else:
            acState = pState
            seconds = time.time() - lastSec
        if acState == States.RETR:
            print("Rectractin state.." + str(seconds))
            if seconds > total_seconds :
                acState = States.EXTE
                pState = acState
                lastSec = time.time()
        elif acState == States.EXTE:
            print("Extending " + str(seconds))
            pState = States.EXTE
            if seconds > total_seconds:
                acState = States.RETR
                pState = acState
                lastSec = time.time()
        elif acState == States.STOP:
            print("Stop " + str(seconds))
            lastSec = time.time() - seconds

t = threading.Thread(target = updateMotors)
t.daemon = True
try:
    t.start()
    while True:

        ret, frameBuf = camera.read()        # convert color and orientation from openCV format to GRAYSCALE

        frame = np.rot90(np.fliplr(frameBuf))
        gray = cv2.cvtColor(frameBuf, cv2.COLOR_BGR2GRAY)
        surface = pygame.surfarray.make_surface(frame)
        # resets video stream buffer
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        faceLen = len(faces)
        for (x,y,w,h) in faces:
            pygame.draw.rect(surface, (255,0,0), [x,y,w,h],2)
            #cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)

            for (ex,ey,ew,eh) in eyes:
                #cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
                pygame.draw.rect(surface, (0,0,255), [x+ex,y+ey,ew,eh],2)
        # make a pygame surface from image
        # prepare surface to display
        screen.fill([0,0,0])

        stateText = ''
        if acState == States.RETR:
            stateText = "Retracting state: " + "{:0.2f}".format(seconds)
        elif acState == States.EXTE:
            stateText = "Extending state:  " + "{:0.2f}".format(seconds)
        elif acState == States.STOP:
            stateText = "Stop:             " + "{:0.2f}".format(seconds)

        text = font.render(stateText, True, (255,0,0))
        py = seconds*(screen_height-2*top_margin)/total_seconds
        screen.blit(text, (2*left_margin + 750, top_margin + py))

        screen.blit(surface, (left_margin, top_margin))

        pygame.display.update()
        # stop programme if esc key has been pressed
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise SystemExit
# this is some magic code that detects when user hits ctrl-c (and stops the programme)
except KeyboardInterrupt,SystemExit:
    t.join()
    pygame.quit()
    cv2.destroyAllWindows()
    sys.exit(0)

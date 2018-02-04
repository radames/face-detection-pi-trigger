import pygame
import cv2
import numpy as np
import sys
import time
import io
import os
import threading

import picamera
import picamera.array
import gpiozero
# set up the camera
time.sleep(1)
camera = picamera.PiCamera()
camera.resolution = (750, 750)
camera.framerate = 15
# set up a video stream
video = picamera.array.PiRGBArray(camera)
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarcascade_eye.xml")
# set up pygame, the library for displaying images
pygame.init()
pygame.display.set_caption("OpenCV camera stream on Pygame")
# sets up window dimensions based on camera resolution
screen = pygame.display.set_mode(list(camera.resolution))
# variables for drawing onto the screen
screen_width = 750
screen_height = 750
pin6 = gpiozero.DigitalOutputDevice(6, active_high=False)
pin5 = gpiozero.DigitalOutputDevice(5, active_high=False)
class States:
    RETR,EXTE,STOP = range(3)
faceLen = 0
def updateMotors():
    global faceLen
    acState = States.RETR
    pState = States.RETR
    sec = 0
    lastSec = time.time()
    while True:
        if faceLen > 0:
            acState = States.STOP
        else:
            acState = pState
            sec = time.time() - lastSec
        if acState == States.RETR:
            print("Rectractin state.." + str(sec))
            pin5.off()
            pin6.on()
            if sec > 15.0 :
                acState = States.EXTE
                pState = acState
                lastSec = time.time()
        elif acState == States.EXTE:
            print("Extending " + str(sec))
            pin5.on()
            pin6.off()
            pState = States.EXTE
            if sec > 15.0:
                acState = States.RETR
                pState = acState
                lastSec = time.time()
        elif acState == States.STOP:
            pin5.off()
            pin6.off()
            print("Stop " + str(sec))
            lastSec = time.time() -sec
t = threading.Thread(target = updateMotors)
t.daemon = True
try:
    t.start()
    for frameBuf in camera.capture_continuous(video, format ="rgb", use_video_port=True):
        # convert color and orientation from openCV format to GRAYSCALE
        frame = np.rot90(np.fliplr(frameBuf.array))
        video.truncate(0)
        gray = cv2.cvtColor(frameBuf.array, cv2.COLOR_BGR2GRAY)
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
            if len(eyes) > 0:
                pin5.off()
                pin6.off()
            for (ex,ey,ew,eh) in eyes:
                #cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
                pygame.draw.rect(surface, (0,0,255), [x+ex,y+ey,ew,eh],2)
        # make a pygame surface from image
        # prepare surface to display
        screen.fill([0,0,0])
        screen.blit(surface, (0,0))
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

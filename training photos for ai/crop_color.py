import cv2
import numpy as np
from color_detection import findColor

cropping = False
get_rect = False
x_start, y_start, x_end, y_end = 0, 0, 0, 0

lower = [0, 0, 0]
upper = [179, 255, 255]
def empty(a):
    lower[0] = cv2.getTrackbarPos("Hue Min", "TrackBars")
    lower[1] = cv2.getTrackbarPos("Sat Min", "TrackBars")
    lower[2] = cv2.getTrackbarPos("Val Min", "TrackBars")
    upper[0] = cv2.getTrackbarPos("Hue Max", "TrackBars")
    upper[1] = cv2.getTrackbarPos("Sat Max", "TrackBars")
    upper[2] = cv2.getTrackbarPos("Val Max", "TrackBars")

def initTrackbars():
    """
    To intialize Trackbars . Need to run only once
    """
    cv2.namedWindow("TrackBars")
    cv2.resizeWindow("TrackBars",640,240)
    cv2.createTrackbar("Hue Min","TrackBars",0,179,empty)
    cv2.createTrackbar("Hue Max","TrackBars",179,179,empty)
    cv2.createTrackbar("Sat Min","TrackBars",0,255,empty)
    cv2.createTrackbar("Sat Max","TrackBars",255,255,empty)
    cv2.createTrackbar("Val Min","TrackBars",0,255,empty)
    cv2.createTrackbar("Val Max","TrackBars",255,255,empty)

def click_and_crop(event, x, y, flags, param):
    # EVENT_LBUTTONDOWN = 1           Left click
    # EVENT_LBUTTONUP = 4             Left key release
    # EVENT_MOUSEMOVE = 0             slide
    global cropping, get_rect, x_start, y_start, x_end, y_end

    if event == cv2.EVENT_LBUTTONDOWN:
        cropping = True
        x_start, y_start, x_end, y_end = x, y, x, y
    elif event == cv2.EVENT_MOUSEMOVE and cropping:
        x_end, y_end = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        x_end, y_end = x, y
        cropping = False
        get_rect = True
    #print(event)

def crop_color(image):
    global get_rect, cropping, x_start, x_end, y_end, y_start
    #image = cv2.imread("resources/shapes.png")
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", click_and_crop)

    while True:
        clone_image = image.copy()  
        if cropping or get_rect:
            cv2.rectangle(clone_image, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)

        cv2.imshow("Image", clone_image)
        key = cv2.waitKey(1)
        if key == 27 & 0xFF:
            break
        if key == ord('c') & 0xFF:
            get_rect = False
            break

    if (x_start, y_start) != (x_end, y_end):
        rect = clone_image[y_start:y_end, x_start:x_end]
        hsv_rect = cv2.cvtColor(rect, cv2.COLOR_BGR2HSV)
        lower = (hsv_rect[:, :, 0].min(), hsv_rect[:, :, 1].min(), hsv_rect[:, :, 2].min())
        upper = (hsv_rect[:, :, 0].max(), hsv_rect[:, :, 1].max(), hsv_rect[:, :, 2].max())
    
    return lower, upper
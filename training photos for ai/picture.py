import cv2
import color_detection as cd
import contour_detection as co
import crop_color as cc
import object_detection as od
import numpy as np
from pathlib import Path
from time import time, sleep

lower = [0, 35, 0]
upper = [23, 184, 255]

cap = cv2.VideoCapture(0)
while(cap.isOpened()):
  ret, frame = cap.read()
  cv2.imshow('frame',frame)
  if cv2.waitKey(1) & 0xFF == ord('q'):
    break
  if cv2.waitKey(1) & 0xFF == ord('s'):
    img = frame
    counter = 0
    Path("img").mkdir(parents=True, exist_ok=True)
    filename = "img" + "/img_" + str(counter) + ".png"
    cv2.imwrite(filename, img)
    sleep(0.2)
    counter += 1

mask, img_color = cd.findColor(img, lower, upper)

cv2.imshow('mask', mask)
cv2.imshow('colored', img_color)
cv2.waitKey(-1)

cap.release()
cv2.destroyAllWindows()

#img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# # detect circles
# gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 5)
# circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=50, minRadius=0, maxRadius=0)
# circles = np.uint16(np.around(circles))

# # draw mask
# mask = np.full((img.shape[0], img.shape[1]), 0, dtype=np.uint8)  # mask is only 
# for i in circles[0, :]:
#     cv2.circle(mask, (i[0], i[1]), i[2], (255, 255, 255), -1)

# # get first masked value (foreground)
# fg = cv2.bitwise_or(img, img, mask=mask)

# # get second masked value (background) mask must be inverted
# mask = cv2.bitwise_not(mask)
# background = np.full(img.shape, 255, dtype=np.uint8)
# bk = cv2.bitwise_or(background, background, mask=mask)

# # combine foreground+background
# final = cv2.bitwise_or(fg, bk)

# cv2.imshow('mask', final)
# cv2.waitKey(-1)
# cv2.destroyAllWindows()
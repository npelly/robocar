import cv2
import matplotlib.pyplot as pyplot


DPI = 80
WINDOW_WIDTH_PX = 1600
WINDOW_HEIGHT_PX= 1200
IMAGE_WIDTH = 320

position = 0
def showSmallImage(image):
    global position

    if position == 0:
        pyplot.figure(figsize = (WINDOW_WIDTH_PX/DPI, WINDOW_HEIGHT_PX/DPI), dpi=DPI)

    pyplot.subplot(3, 4, position + 1)
    pyplot.axis('off')

    pyplot.subplots_adjust(top = 1.0, bottom = 0.0, right = 1.0, left = 0.0,
            hspace = 0.0, wspace = 0.0)

    if len(image.shape) == 3:
        # assume cv2 BGR, fix
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pyplot.imshow(image)
    elif len(image.shape) == 2:
        pyplot.imshow(image, cmap='gray')


    pyplot.show(block=False)
    position += 1

def pause():
    global position
    raw_input("Press any key to continue")
    position = 0

def closeOnInput():
    global position
    raw_input("Press any key to close")
    pyplot.close()
    position = 0

def test():
    image = cv2.imread("test-pic-1.jpg")
    showSmallImage(image)
    showSmallImage(image)
    closeOnInput()

if __name__ == "__main__":
    test()

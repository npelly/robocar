import pygame
import sys
import time
import motor

FAST = 0xFF
SLOW = 0xB0

pygame.init()

# set up the window
windowSurface = pygame.display.set_mode((400, 50))
pygame.display.set_caption("Keyboard capture")

# render text
WHITE = (255, 255, 255)
basicFont = pygame.font.SysFont("monospace", 32)
text = basicFont.render("<keyboard capture>", True, WHITE)

# draw the text onto the surface
windowSurface.blit(text, (0, 0))

# draw the window onto the screen
pygame.display.update()

motor = motor.get_default_motor()

# run the game loop
running = True
lastLeft = 0x00
lastRight = 0x00
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            running = False
    if not running: break
    keys = pygame.key.get_pressed()

    left = 0x00
    right = 0x00
    if keys[pygame.K_w]:
        left = SLOW
        right = SLOW
    if keys[pygame.K_s]:
        left = -SLOW
        right = -SLOW
    if keys[pygame.K_a]:
        right = FAST
    if keys[pygame.K_d]:
        left = FAST

    if lastLeft != left or lastRight != right:
        motor.drive(left, right)
    lastLeft = left
    lastRight = right

motor.close()
pygame.quit()
sys.exit()

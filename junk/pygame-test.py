import pygame
import sys

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

# run the game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            print event.key
            if event.key == pygame.K_q:
                running = False

pygame.quit()
sys.exit()

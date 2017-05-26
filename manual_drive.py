import pygame
import sys
import time


import robocore.motor
import robocore.car_model

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

if robocore.util.isRaspberryPi():
    motor = robocore.motor.ArduinoSerialMotor()
else:
    motor = robocore.motor.DummyMotor()

with motor:
    prev_left_power = 0x00
    prev_right_power = 0x00
    running = True
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
        if not running: break

        keys = pygame.key.get_pressed()

        left_power = 0x00
        right_power = 0x00
        if keys[pygame.K_w]:
            left_power = SLOW
            right_power = SLOW
        if keys[pygame.K_s]:
            left_power = -SLOW
            right_power = -SLOW
        if keys[pygame.K_a]:
            right_power = FAST
        if keys[pygame.K_d]:
            left_power = FAST

        if prev_left_power != left_power or prev_right_power != right_power:
            instruction = robocore.car_model.Instruction(left_power, right_power)
            motor.process(instruction)
            print instruction
        prev_left_power = left_power
        prev_right_power = right_power

pygame.quit()
sys.exit()

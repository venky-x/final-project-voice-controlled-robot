import pygame
import time
import sys

# Initialize Pygame
pygame.init()

# Set up the display in fullscreen mode
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)

pygame.display.set_caption("EMO Robot Eyes")

# Colors (background white, eyes/mouth black)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def draw_eyes_and_mouth(screen, eye_state, look_direction):
    """Draw animated eyes and mouth based on state and direction."""
    # Set white background
    screen.fill(WHITE)

    # Get screen dimensions dynamically
    width, height = screen.get_size()

    # Eye positions (centered, scaled to screen size)
    eye_radius = min(width, height) // 7
    pupil_radius = eye_radius // 2
    left_eye_x = width // 4
    left_eye_y = height // 3
    right_eye_x = 3 * width // 4
    right_eye_y = height // 3

    if eye_state == "open":
        # Draw eye outlines
        pygame.draw.circle(screen, BLACK, (left_eye_x, left_eye_y), eye_radius, 2)
        pygame.draw.circle(screen, BLACK, (right_eye_x, right_eye_y), eye_radius, 2)

        # Adjust pupil position based on look direction
        pupil_offset = eye_radius // 2
        if look_direction == "left":
            pupil_left_x = left_eye_x - pupil_offset
            pupil_right_x = right_eye_x - pupil_offset
        elif look_direction == "right":
            pupil_left_x = left_eye_x + pupil_offset
            pupil_right_x = right_eye_x + pupil_offset
        else:  # center
            pupil_left_x = left_eye_x
            pupil_right_x = right_eye_x

        # Draw pupils
        pygame.draw.circle(screen, BLACK, (pupil_left_x, left_eye_y), pupil_radius)
        pygame.draw.circle(screen, BLACK, (pupil_right_x, right_eye_y), pupil_radius)
    elif eye_state == "blink":
        # Draw closed eyes (lines)
        pygame.draw.line(screen, BLACK, (left_eye_x - eye_radius, left_eye_y),
                        (left_eye_x + eye_radius, left_eye_y), 2)
        pygame.draw.line(screen, BLACK, (right_eye_x - eye_radius, right_eye_y),
                        (right_eye_x + eye_radius, right_eye_y), 2)

    # Draw mouth (arc with flat top)
    mouth_y = height * 2 // 2.3
    mouth_width = eye_radius * 4
    mouth_height = eye_radius * 3
    center_x = width // 2

    # Draw the arc (upward curve)
    pygame.draw.arc(screen, BLACK, (center_x - mouth_width // 2, mouth_y - mouth_height,
                                  mouth_width, mouth_height), 3.14, 6.28, 4)

    # Draw horizontal line at a lower position
    top_y = mouth_y - (mouth_height // 2)  # Lower the line by half the height
    pygame.draw.line(screen, BLACK, (center_x - mouth_width // 2, top_y),
                    (center_x + mouth_width // 2, top_y), 4)

    # Update the display
    pygame.display.flip()

# Main animation loop
try:
    eye_state = "open"
    look_direction = "center"
    frame = 0
    clock = pygame.time.Clock()

    while True:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Update animation every few frames
        frame += 1

        # Blink every 30 frames (~3 seconds at 10 FPS)
        if frame % 30 == 0:
            eye_state = "blink"
        elif frame % 30 == 2:
            eye_state = "open"

        # Change look direction every 50 frames (~5 seconds at 10 FPS)
        if frame % 50 == 0:
            if look_direction == "center":
                look_direction = "left"
            elif look_direction == "left":
                look_direction = "right"
            else:
                look_direction = "center"

        # Draw the current frame
        draw_eyes_and_mouth(screen, eye_state, look_direction)

        # Control frame rate (~10 FPS)
        clock.tick(10)

except KeyboardInterrupt:
    # Clear the screen on exit
    screen.fill(WHITE)
    pygame.display.flip()
    pygame.quit()
    sys.exit(0)

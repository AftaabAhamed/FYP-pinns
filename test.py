import raylibpy as rl
from math import sin, cos, radians

# Initialization
screen_width = 800
screen_height = 600
rl.init_window(screen_width, screen_height, "FPV Perspective with Ball")

# Camera setup
camera_position = rl.Vector3(0.0, 2.0, 5.0)  # Camera's position
camera_target = rl.Vector3(0.0, 2.0, 0.0)    # Camera's target (where it's looking)
camera_up = rl.Vector3(0.0, 1.0, 0.0)        # Camera's up vector

# Ball setup
ball_position = rl.Vector3(0.0, 1.0, 0.0)
ball_radius = 0.5

# Variables for camera movement
camera_yaw = 0.0
camera_pitch = 0.0
move_speed = 0.1
mouse_sensitivity = 0.2

# Enable the mouse cursor to be hidden and centered
rl.set_mouse_position(screen_width // 2, screen_height // 2)
rl.disable_cursor()

rl.set_target_fps(60)

# Main game loop
while not rl.window_should_close():
    # Update mouse look
    mouse_delta = rl.get_mouse_delta()
    camera_yaw -= mouse_delta.x * mouse_sensitivity
    camera_pitch += mouse_delta.y * mouse_sensitivity

    # Clamp pitch to prevent flipping
    camera_pitch = max(-89.0, min(89.0, camera_pitch))

    # Calculate forward and right vectors based on yaw and pitch
    forward = rl.Vector3(
        cos(radians(camera_yaw)) * cos(radians(camera_pitch)),
        sin(radians(camera_pitch)),
        sin(radians(camera_yaw)) * cos(radians(camera_pitch))
    )
    right = rl.Vector3(
        cos(radians(camera_yaw - 90)),
        0.0,
        sin(radians(camera_yaw - 90))
    )

    # Normalize forward and right vectors
    forward = rl.vector3_normalize(forward)
    right = rl.vector3_normalize(right)

    # Handle keyboard input for movement
    if rl.is_key_down(rl.KEY_W):
        camera_position = rl.vector3_add(camera_position, rl.vector3_scale(forward, move_speed))
    if rl.is_key_down(rl.KEY_S):
        camera_position = rl.vector3_subtract(camera_position, rl.vector3_scale(forward, move_speed))
    if rl.is_key_down(rl.KEY_A):
        camera_position = rl.vector3_subtract(camera_position, rl.vector3_scale(right, move_speed))
    if rl.is_key_down(rl.KEY_D):
        camera_position = rl.vector3_add(camera_position, rl.vector3_scale(right, move_speed))

    # Update the camera target
    camera_target = rl.vector3_add(camera_position, forward)

    # Draw
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)

    # Begin 3D mode
    rl.begin_mode3d(rl.Camera(camera_position, camera_target, camera_up, 60.0, rl.CAMERA_PERSPECTIVE))

    # Draw the ball
    rl.draw_sphere(ball_position, ball_radius, rl.RED)

    # Draw the ground
    rl.draw_plane(rl.Vector3(0.0, 0.0, 0.0), rl.Vector2(10.0, 10.0), rl.LIGHTGRAY)

    rl.end_mode3d()

    # Instructions
    rl.draw_text("Move with WASD, look around with mouse", 10, 10, 20, rl.DARKGRAY)

    rl.end_drawing()

# De-Initialization
rl.close_window()

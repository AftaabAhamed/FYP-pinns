import raylibpy as rl
import math
import time
import csv
from datetime import datetime

class SphericalTankVisualizer:
    """3D Spherical Tank Visualization with adjustable water level."""

    def __init__(self, screen_width=800, screen_height=600, sphere_diameter_cm=17.38 * 25, cylinder_height_cm=20.0):
        # Constants and parameters
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sphere_diameter_cm = sphere_diameter_cm
        self.cylinder_height_cm = cylinder_height_cm
        self.sphere_radius = self.sphere_diameter_cm / 100.0 / 2.0  # Radius of the sphere in meters
        self.cylinder_height = self.cylinder_height_cm / 100.0  # Height of the cylinder in meters
        self.water_segments = 500  # Number of segments to approximate the water fill

        # Camera setup
        self.camera = rl.Camera(
            position=rl.Vector3(6.0, 6.0, 6.0),
            target=rl.Vector3(0.0, 0.0, 0.0),
            up=rl.Vector3(0.0, 1.0, 0.0),
            fovy=45.0,
            projection=rl.CAMERA_PERSPECTIVE,
        )

    def draw(self, water_height, time):
        """Draws the spherical tank and water level based on the given height."""
        # water_height = (water_height_cm - (self.sphere_diameter_cm / 2.0)) / 100.0  # Convert to meters

        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)

        rl.begin_mode3d(self.camera)

        # Draw the transparent spherical tank
        rl.draw_sphere(rl.Vector3(0, 0, 0), self.sphere_radius, rl.Color(200, 200, 255, 60))
        rl.draw_sphere_wires(rl.Vector3(0, 0, 0), self.sphere_radius, 16, 16, rl.DARKGRAY)

        # Draw water level
        self.draw_water_level(water_height)

        # Draw the top cylinder above the sphere
        self.draw_top_cylinder(self.sphere_radius + self.cylinder_height - 0.15, self.cylinder_height)

        rl.end_mode3d()

        # Display information
        rl.draw_text(f"Water Height: {water_height*100:.5f} cm", 10, 10, 20, rl.DARKGRAY)
        rl.draw_text(f"Time: {time}", 10, 40, 20, rl.DARKGRAY)

        rl.end_drawing()

    def draw_water_level(self, height):
        """Draws water up to the specified height inside the spherical tank."""
        if height < -self.sphere_radius:
            height = -self.sphere_radius
        elif height > self.sphere_radius:
            height = self.sphere_radius

        step = (2 * self.sphere_radius) / self.water_segments
        for y in range(self.water_segments):
            current_height = -self.sphere_radius + y * step
            if current_height <= height:
                disk_radius = math.sqrt(self.sphere_radius**2 - current_height**2)
                rl.draw_cylinder(rl.Vector3(0, current_height, 0), disk_radius, disk_radius, 0.01, 16, rl.BLUE)

    def draw_top_cylinder(self, position, height):
        """Draws a cylinder at a specified position above the sphere."""
        rl.draw_cylinder(
            rl.Vector3(0, position, 0),
            self.sphere_radius / 2,
            self.sphere_radius / 2,
            height,
            16,
            rl.Color(200, 200, 255, 60),
        )
        rl.draw_cylinder_wires(
            rl.Vector3(0, position, 0),
            self.sphere_radius / 2,
            self.sphere_radius / 2,
            height,
            256,
            rl.DARKGRAY,
        )


def main():
    visualizer = SphericalTankVisualizer()
    rl.init_window(visualizer.screen_width, visualizer.screen_height, "3D Tank Visualization")
    rl.set_target_fps(60)

    # Simulate water level changes using a for loop
    water_levels = list(range(0, int(visualizer.sphere_diameter_cm) + 1)) + list(range(int(visualizer.sphere_diameter_cm), -1, -1))
    curr_time = 10

    while True:
        if rl.window_should_close():
            break

        # Read csv file for last input
        with open('./data/Differential_data.csv') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                water_height_cm = float(last_row[1])

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        visualizer.draw(water_height_cm, str(current_time))
    rl.close_window()


if __name__ == "__main__":
    main()

import cv2
import numpy as np
import requests
import math

# --- Configuration ---
WIDTH, HEIGHT = 1200, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
SCALE = 150  # pixels per AU
SUN_RADIUS = 15
ASTEROID_RADIUS = 3
EARTH_ORBIT_RADIUS = 1.0 * SCALE

# List of interesting asteroid IDs (433 is Eros)
ASTEROID_IDS = ['433', '99942']  # Eros and Apophis

# --- Fetch Data ---
asteroids_data = []
for aid in ASTEROID_IDS:
    data = fetch_asteroid_data(aid)
    if data:
        asteroids_data.append(data)
    print(f"Fetched data for {data['name']}")


# --- Animation Function ---
def calculate_position(orbit_params, angle_rad):
    """Calculates x, y position in 2D for a given true anomaly."""
    a = orbit_params['semi_major_axis']
    e = orbit_params['eccentricity']
    r = (a * (1 - e ** 2)) / (1 + e * np.cos(angle_rad))  # Polar equation of ellipse
    x = r * np.cos(angle_rad)
    y = r * np.sin(angle_rad)
    # Convert to image coordinates
    img_x = CENTER[0] + int(x * SCALE)
    img_y = CENTER[1] - int(y * SCALE)  # Subtract because image y-axis is down
    return (img_x, img_y)


# Initialize angles for each asteroid
angles = [0] * len(asteroids_data)

while True:
    # Create a blank image
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # 1. Draw static elements
    cv2.circle(frame, CENTER, SUN_RADIUS, (0, 255, 255), -1)
    cv2.circle(frame, CENTER, int(EARTH_ORBIT_RADIUS), (100, 100, 255), 1)

    # 2. Draw orbits and animated asteroids
    for i, ast in enumerate(asteroids_data):
        color = (0, 0, 255)  # Red for asteroids
        draw_orbit(ast, color, frame)

        # Calculate and draw current position
        pos = calculate_position(ast, angles[i])
        cv2.circle(frame, pos, ASTEROID_RADIUS, (0, 255, 0), -1)  # Green dot

        # Draw a label
        label = f"{ast['name']}"
        cv2.putText(frame, label, (pos[0] + 10, pos[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Update the angle for the next frame (animate)
        angles[i] += 0.01 / ast['semi_major_axis']  # Kepler's law: outer planets move slower

    # 3. Display info panel
    y_offset = 30
    cv2.putText(frame, "NASA Asteroid Tracker Simulation", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2)
    y_offset += 30
    for ast in asteroids_data:
        info_text = f"{ast['name']}: a={ast['semi_major_axis']} AU, e={ast['eccentricity']}, d~{ast['diameter_km']} km"
        cv2.putText(frame, info_text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 25

    # 4. Show the frame
    cv2.imshow('NASA Asteroid Tracker', frame)

    # 5. Exit on 'q' key
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
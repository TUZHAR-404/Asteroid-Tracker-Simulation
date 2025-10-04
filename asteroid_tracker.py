import cv2
import numpy as np
import requests
import json

# --- Configuration ---
WIDTH, HEIGHT = 1200, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
SCALE = 150  # pixels per Astronomical Unit (AU)
SUN_RADIUS = 15
ASTEROID_RADIUS = 5
EARTH_ORBIT_RADIUS = 1.0 * SCALE

# List of interesting asteroid NASA JPL IDs with backup options
ASTEROID_IDS = ['433', '2000216', '202136']  # Eros, Bennu, and another known NEO


# --- Function to Fetch Data from NASA API ---
def fetch_asteroid_data(asteroid_id):
    """
    Fetches orbital data for a specific asteroid from NASA's SBDB API.
    """
    url = f"https://ssd-api.jpl.nasa.gov/sbdb.api?sstr={asteroid_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Debug: print the entire response to see what we get
        print(f"API Response for {asteroid_id}:")
        print(json.dumps(data, indent=2)[:500] + "...")  # Print first 500 chars

        orbit_data = data.get('orbit', {})
        physical_data = data.get('physical_parameters', {})

        name = data.get('object', {}).get('fullname', f'NEO {asteroid_id}')

        # Safely extract orbital parameters with default values
        a_str = orbit_data.get('a', '0')
        e_str = orbit_data.get('e', '0')
        i_str = orbit_data.get('i', '0')

        try:
            a = float(a_str) if a_str else 1.0  # Default to 1.0 if empty
            e = float(e_str) if e_str else 0.1  # Default to 0.1 if empty
            i = float(i_str) if i_str else 5.0  # Default to 5.0 if empty
        except ValueError:
            print(f"Warning: Could not convert orbital parameters for {asteroid_id}")
            a, e, i = 1.0, 0.1, 5.0  # Safe defaults

        diameter_km = "Unknown"
        if physical_data and 'diameter' in physical_data:
            try:
                diameter_km = f"{float(physical_data.get('diameter', 0)):.3f}"
            except ValueError:
                diameter_km = "Unknown"

        return {
            'name': name,
            'id': asteroid_id,
            'semi_major_axis': a,
            'eccentricity': e,
            'inclination': i,
            'diameter_km': diameter_km,
            'data_quality': 'real' if a > 0 else 'simulated'
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {asteroid_id}: {e}")
        # Return simulated data if API fails
        return create_simulated_asteroid(asteroid_id)


def create_simulated_asteroid(asteroid_id):
    """Create simulated asteroid data when real data is unavailable"""
    simulated_data = {
        '433': {'name': '433 Eros (Simulated)', 'a': 1.46, 'e': 0.23, 'i': 10.8},
        '2000216': {'name': '101955 Bennu (Simulated)', 'a': 1.13, 'e': 0.20, 'i': 6.0},
        '202136': {'name': 'NEO 202136 (Simulated)', 'a': 1.20, 'e': 0.15, 'i': 3.5}
    }

    if asteroid_id in simulated_data:
        data = simulated_data[asteroid_id]
        return {
            'name': data['name'],
            'id': asteroid_id,
            'semi_major_axis': data['a'],
            'eccentricity': data['e'],
            'inclination': data['i'],
            'diameter_km': 'Simulated',
            'data_quality': 'simulated'
        }
    else:
        # Generic simulated asteroid
        return {
            'name': f'Asteroid {asteroid_id} (Simulated)',
            'id': asteroid_id,
            'semi_major_axis': 1.5 + (int(asteroid_id) % 10) * 0.2 if asteroid_id.isdigit() else 2.0,
            'eccentricity': 0.1 + (int(asteroid_id) % 10) * 0.05 if asteroid_id.isdigit() else 0.2,
            'inclination': 5.0 + (int(asteroid_id) % 10) * 2.0 if asteroid_id.isdigit() else 8.0,
            'diameter_km': 'Simulated',
            'data_quality': 'simulated'
        }


# --- Function to Draw an Orbit ---
def draw_orbit(orbit_params, color, img):
    """
    Draws an elliptical orbit based on semi-major axis (a) and eccentricity (e).
    """
    a_pixels = orbit_params['semi_major_axis'] * SCALE
    e = orbit_params['eccentricity']

    # Ensure valid values for drawing
    if a_pixels <= 0:
        a_pixels = 1.0 * SCALE
    if e >= 1.0:  # Hyperbolic orbit (some NEOs)
        e = 0.9

    b_pixels = a_pixels * np.sqrt(1 - e ** 2)

    center_x = CENTER[0] + int(a_pixels * e)
    center_y = CENTER[1]

    axes = (int(a_pixels), int(b_pixels))
    cv2.ellipse(img, (center_x, center_y), axes, 0, 0, 360, color, 1)


# --- Function to Calculate Asteroid Position ---
def calculate_position(orbit_params, angle_rad):
    """Calculates x, y position in 2D for a given true anomaly."""
    a = max(orbit_params['semi_major_axis'], 0.1)  # Ensure minimum value
    e = min(max(orbit_params['eccentricity'], 0), 0.99)  # Ensure valid range

    r = (a * (1 - e ** 2)) / (1 + e * np.cos(angle_rad))
    x = r * np.cos(angle_rad)
    y = r * np.sin(angle_rad)
    img_x = CENTER[0] + int(x * SCALE)
    img_y = CENTER[1] - int(y * SCALE)
    return (img_x, img_y)


# --- MAIN PROGRAM ---
print("Fetching data from NASA JPL...")
asteroids_data = []
for aid in ASTEROID_IDS:
    data = fetch_asteroid_data(aid)
    if data:
        asteroids_data.append(data)
        quality = data['data_quality']
        print(f"✓ {'SIMULATED' if quality == 'simulated' else 'REAL'} data for {data['name']}")
        print(f"  a={data['semi_major_axis']} AU, e={data['eccentricity']}")
    else:
        print(f"✗ Failed to fetch data for ID: {aid}")

# Check if we have data before starting
if not asteroids_data:
    print("No asteroid data available. Creating simulated data...")
    asteroids_data = [create_simulated_asteroid('test')]

# Initialize angles for animation
angles = [np.random.random() * 2 * np.pi for _ in asteroids_data]  # Random starting positions
print("\nSimulation started! Press 'q' to quit.")

# Main animation loop
while True:
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # 1. Draw static elements
    cv2.circle(frame, CENTER, SUN_RADIUS, (0, 255, 255), -1)
    cv2.putText(frame, "Sun", (CENTER[0] - 15, CENTER[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.circle(frame, CENTER, int(EARTH_ORBIT_RADIUS), (100, 100, 255), 1)
    earth_pos = (CENTER[0] + int(EARTH_ORBIT_RADIUS), CENTER[1])
    cv2.circle(frame, earth_pos, 4, (255, 100, 0), -1)
    cv2.putText(frame, "Earth", (earth_pos[0] + 5, earth_pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 2. Draw orbits and animated asteroids
    for i, ast in enumerate(asteroids_data):
        orbit_color = (0, 100, 255) if ast['data_quality'] == 'real' else (100, 100, 100)
        draw_orbit(ast, orbit_color, frame)

        # Calculate and draw current position
        pos = calculate_position(ast, angles[i])
        dot_color = (0, 255, 0) if ast['data_quality'] == 'real' else (200, 200,
                                                                       200)  # Green for real, gray for simulated
        cv2.circle(frame, pos, ASTEROID_RADIUS, dot_color, -1)

        # Draw a label
        label = f"{ast['name']}"
        cv2.putText(frame, label, (pos[0] + 10, pos[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Safe animation update
        speed_factor = 0.01 / max(ast['semi_major_axis'], 0.1)  # Prevent division by zero
        angles[i] += speed_factor

    # 3. Display info panel
    y_offset = 30
    cv2.putText(frame, "NASA Asteroid Tracker Simulation", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                (255, 255, 255), 2)
    y_offset += 40

    for ast in asteroids_data:
        quality_text = "REAL DATA" if ast['data_quality'] == 'real' else "SIMULATED DATA"
        color = (0, 255, 0) if ast['data_quality'] == 'real' else (200, 200, 200)
        cv2.putText(frame, quality_text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y_offset += 25

        info_text = f"{ast['name']} (ID: {ast['id']}): a={ast['semi_major_axis']:.3f} AU, e={ast['eccentricity']:.3f}"
        cv2.putText(frame, info_text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        y_offset += 30

        dia_text = f"    Diameter: ~{ast['diameter_km']} km | Inclination: {ast['inclination']:.2f} deg"
        cv2.putText(frame, dia_text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        y_offset += 25

    y_offset += 10
    cv2.putText(frame, "Press 'q' to quit. Green = Real API data, Gray = Simulated data", (20, HEIGHT - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 255), 1)

    # 4. Show the frame
    cv2.imshow('NASA Asteroid Tracker', frame)

    # 5. Exit on 'q' key press
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print("Simulation closed.")
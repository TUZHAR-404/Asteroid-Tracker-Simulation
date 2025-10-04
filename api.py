import requests
import json


def fetch_asteroid_data(asteroid_id):
    """
    Fetches orbital data for a specific asteroid from NASA's SBDB API.
    """
    url = f"https://ssd-api.jpl.nasa.gov/sbdb.api?sstr={asteroid_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad status codes
        data = response.json()

        # Extract orbital parameters. The API structure is nested.
        orbit_data = data.get('orbit', {})
        physical_data = data.get('physical_parameters', {})

        # Get name and ID
        name = data.get('object', {}).get('fullname', 'N/A')

        # Get crucial orbital elements
        a = float(orbit_data.get('a', 0))  # semi-major axis (AU)
        e = float(orbit_data.get('e', 0))  # eccentricity
        i = float(orbit_data.get('i', 0))  # inclination (degrees)

        # Get estimated diameter (if available)
        diameter_km = "N/A"
        if physical_data and 'diameter' in physical_data:
            diameter_km = f"{float(physical_data.get('diameter')):.3f}"

        return {
            'name': name,
            'id': asteroid_id,
            'semi_major_axis': a,
            'eccentricity': e,
            'inclination': i,
            'diameter_km': diameter_km
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {asteroid_id}: {e}")
        return None


# Example: Fetch data for a famous NEO (Eros)
eros_data = fetch_asteroid_data('433')
print(eros_data)
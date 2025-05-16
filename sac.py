import os
import obspy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from obspy.clients.fdsn import Client
from mpl_toolkits.basemap import Basemap

# Set environment variables
os.environ['PROJ_LIB'] = 'C:\\Users\\Denise\\Desktop\\SAC'

# Output folder
folder_output = 'C:\\Users\\Denise\\Desktop\\SAC\\Output'
os.makedirs(folder_output, exist_ok=True)

# Excel file details
excel_filename = 'calmex.xlsx'
excel_tab = 'info'

# Define search parameters
starttime = obspy.UTCDateTime("1970-01-01")
endtime = obspy.UTCDateTime("2025-02-01")
minlatitude, maxlatitude = 10.0, 50.0
minlongitude, maxlongitude = -130.0, -85.0
minmagnitude, maxmagnitude = 5.0, 9.5

# Fetch events using IRIS client
client = Client("IRIS")

try:
    events = client.get_events(minlatitude=minlatitude, maxlatitude=maxlatitude,
                               minlongitude=minlongitude, maxlongitude=maxlongitude,
                               starttime=starttime, endtime=endtime,
                               minmagnitude=minmagnitude, maxmagnitude=maxmagnitude)
    print(f"Found {len(events)} event(s):")
except Exception as e:
    print(f"Error fetching events: {e}")
    events = []

# Store data in DataFrame
feature_list = ['Origin Time (UTC)', 'Lat [°]', 'Lon [°]', 'Depth [m]', 'Event Type', 'Magnitude', 'Magnitude Type', 'Creation Info', 'Info']
df = pd.DataFrame(columns=feature_list)

for event in events:
    try:
        origin = event.origins[0]
        magnitude = event.magnitudes[0]
        
        # Validate magnitude range
        if not (minmagnitude <= magnitude.mag <= maxmagnitude):
            continue
        
        new_row = pd.DataFrame({
            'Origin Time (UTC)': [origin.time],
            'Lat [°]': [origin.latitude],
            'Lon [°]': [origin.longitude],
            'Depth [m]': [origin.depth],
            'Event Type': [event.event_type if event.event_type else 'Unknown'],
            'Magnitude': [magnitude.mag],
            'Magnitude Type': [magnitude.magnitude_type if magnitude.magnitude_type else 'N/A'],
            'Creation Info': [origin.creation_info if hasattr(origin, 'creation_info') else 'N/A'],
            'Info': [event.event_descriptions[0].text if event.event_descriptions else 'N/A']
        })
        df = pd.concat([df, new_row], ignore_index=True)
    except Exception as e:
        print(f"Error processing event: {e}")

# Save to Excel
excel_output = os.path.join(folder_output, excel_filename)
df.to_excel(excel_output, sheet_name=excel_tab, index=False)

# Plot events on map
if not df.empty:
    plt.rcParams.update({'font.size': 14})
    plt.rcParams['axes.labelweight'] = 'bold'

    x, y, z = df['Lon [°]'].values, df['Lat [°]'].values, df['Magnitude'].values
    plt_title = f'Earthquakes {starttime.strftime("%Y-%m-%d")} - {endtime.strftime("%Y-%m-%d")} '
    plt_fig = os.path.join(folder_output, plt_title + '.png')

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, facecolor='w', frame_on=False)
    norm = Normalize()

    # Initialize map
    try:
        map = Basemap(llcrnrlon=minlongitude, llcrnrlat=minlatitude, 
                      urcrnrlon=maxlongitude, urcrnrlat=maxlatitude,
                      projection='merc', resolution='h')
    except Exception as e:
        print(f"Basemap error: {e}")
        exit()
    
    x_lon, y_lat = map(x, y)
    map.drawcoastlines()
    map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(color='grey', lake_color='aqua')
    map.drawcountries(linewidth=0.75, linestyle='solid', color='#000073', zorder=3)
    
    scatter = map.scatter(x_lon, y_lat, c=z, alpha=1, s=200 * norm(z), cmap='jet', vmin=z.min(), vmax=z.max(), zorder=4)
    cbar = map.colorbar(scatter)
    cbar.set_label('Magnitude', size=14)
    plt.title(plt_title, fontweight="bold")
    plt.savefig(plt_fig, bbox_inches='tight', dpi=500)
    plt.show()

# Load SAC files
sac_folder = 'C:\\Users\\Denise\\Downloads\\Cal_Mexico'
if os.path.exists(sac_folder):
    sac_files = [f for f in os.listdir(sac_folder) if f.endswith('.SAC')]
    for sac_file in sac_files:
        try:
            st = obspy.read(os.path.join(sac_folder, sac_file))
            print(st)  # Display SAC file content
        except Exception as e:
            print(f"Error reading {sac_file}: {e}")
else:
    print(f"SAC folder not found: {sac_folder}")

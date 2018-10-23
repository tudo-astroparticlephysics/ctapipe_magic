import matplotlib.pylab as plt

from ctapipe.image import hillas_parameters, tailcuts_clean
from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from ctapipe_magic.magicioeventsource import MAGICIOEventSource

from matplotlib.animation import FuncAnimation

# Load the camera
geom = CameraGeometry.from_table("/data/MAGICII.camgeom.fits.gz")

fig, ax = plt.subplots()

disp = CameraDisplay(geom, ax=ax)
disp.add_colorbar()

# Get the eventsource
evt_source = MAGICIOEventSource(
    # input_url="/data/20181011_M1_05075881.001_Y_CrabNebula-W0.40+359.root"
    input_url="/data/magic_test.root"
)
image = evt_source._generator()


def update(i):
    # Apply image cleaning
    # get a single image
    img = next(image)
    im = img["tel"]["image"]

    cleanmask = tailcuts_clean(
        geom, im, picture_thresh=30, boundary_thresh=5, min_number_picture_neighbors=0
    )

    if sum(cleanmask) == 0:
        print(f"no pixels survived cleaning in image {i}")
    else:
        # Calculate image parameters
        hillas = hillas_parameters(geom[cleanmask], im[cleanmask])

        # Show the camera image and overlay Hillas ellipse and clean pixels
        disp.image = im
        disp.highlight_pixels(cleanmask, color="crimson")
        disp.overlay_moments(hillas, color="red", linewidth=2)


ani = FuncAnimation(fig, update, frames=200, blit=False, repeat=False)
ani.save("build/test.mp4", bitrate=8096, codec="libx264", writer="ffmpeg", fps=25)

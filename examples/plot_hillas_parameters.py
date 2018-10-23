import matplotlib.pylab as plt

from ctapipe.image import hillas_parameters, tailcuts_clean
from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from ctapipe_magic.magicioeventsource import MAGICIOEventSource


if __name__ == "__main__":

    # Load the camera
    geom = CameraGeometry.from_name(camera_id="MAGICCam")

    fig, ax = plt.subplots()

    disp = CameraDisplay(geom, ax=ax)
    disp.add_colorbar()

    # Get the eventsource
    evt_source = MAGICIOEventSource(
        # input_url="/data/20181011_M1_05075881.001_Y_CrabNebula-W0.40+359.root"
        input_url="/data/magic_test.root"
    )
    image = evt_source._generator()

    # get a single image
    for i, img in enumerate(image):
        if i > 147:
            break
    im = img["tel"]["image"]

    # Apply image cleaning
    cleanmask = tailcuts_clean(
        geom, im, picture_thresh=30, boundary_thresh=5, min_number_picture_neighbors=0
    )

    if sum(cleanmask) == 0:
        pass
    else:
        # Calculate image parameters
        hillas = hillas_parameters(geom[cleanmask], im[cleanmask])

        # Show the camera image and overlay Hillas ellipse and clean pixels
        disp.image = im
        disp.highlight_pixels(cleanmask, color="crimson")
        disp.overlay_moments(hillas, color="red", linewidth=2)

        plt.savefig("build/hillas_example.png", dpi=300)

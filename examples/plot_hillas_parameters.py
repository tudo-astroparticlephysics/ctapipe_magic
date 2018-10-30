import matplotlib.pylab as plt

from ctapipe.image import hillas_parameters, tailcuts_clean
from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from ctapipe_magic.magicioeventsource import MAGICIOEventSource


if __name__ == "__main__":

    # Load the camera
    geom = CameraGeometry.from_name(camera_id="MAGICCam")

    fig, (ax1, ax2) = plt.subplots(ncols=2)

    disp1 = CameraDisplay(geom, ax=ax1)
    disp1.add_colorbar()
    disp2 = CameraDisplay(geom, ax=ax2)
    disp2.add_colorbar()

    # Get the eventsource
    source = MAGICIOEventSource(
        # input_url="/data/20181011_M1_05075881.001_Y_CrabNebula-W0.40+359.root"
        input_url="/data/GA_M1_za05to35_9_823708_Y_w0.root"
    )

    # get a single image
    for i, img in enumerate(source):
        # Pick a (random) good looking image
        if i > 147:
            break
    im1 = img.dl1.tel[0].image
    im2 = img.dl1.tel[1].image
    print(img)

    # Apply image cleaning
    cleanmask1 = tailcuts_clean(
        geom, im1, picture_thresh=30, boundary_thresh=5, min_number_picture_neighbors=0
    )
    cleanmask2 = tailcuts_clean(
        geom, im2, picture_thresh=30, boundary_thresh=5, min_number_picture_neighbors=0
    )

    if sum(cleanmask1) == 0:
        pass
    else:
        # Calculate image parameters
        hillas1 = hillas_parameters(geom[cleanmask1], im1[cleanmask1])
        hillas2 = hillas_parameters(geom[cleanmask2], im2[cleanmask2])

        # Show the camera image and overlay Hillas ellipse and clean pixels
        disp1.image = im1
        disp1.highlight_pixels(cleanmask1, color="crimson")
        disp1.overlay_moments(hillas1, color="red", linewidth=2)

        disp2.image = im2
        disp2.highlight_pixels(cleanmask2, color="crimson")
        disp2.overlay_moments(hillas2, color="red", linewidth=2)

        fig.tight_layout()
        fig.savefig("build/hillas_example.png", dpi=200)

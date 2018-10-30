import uproot
from ctapipe.io.eventsource import EventSource
from ctapipe.io.containers import DataContainer
from astropy import units as u

# TODO: Fix Imports
from ctapipe.instrument import SubarrayDescription
from ctapipe.instrument import TelescopeDescription
from ctapipe.instrument import CameraGeometry
from ctapipe.instrument import OpticsDescription


__all__ = ["MAGICIOEventSource"]


class MAGICIOEventSource(EventSource):
    """
    EventSource for the magic file format.

    This class utilises `uproot` to read the magic files, and stores the
    information into the event containers.

    Install `uproot` using `pip`:
    `pip install uproot`
    """

    def __init__(self, config=None, tool=None, **kwargs):
        super().__init__(config=config, tool=tool, **kwargs)

        # TODO: Initialize CameraGeamoetry and OpticsDescription
        # needed for subarray information in
        # data.inst.subarray (but is deprecated?)
        self.camgeom = CameraGeometry.from_name(camera_id="MAGICCam")
        self.optics = OpticsDescription(
            mirror_type="SC",
            tel_type="MST",
            tel_subtype="1M",
            equivalent_focal_length=1 * u.m,
            mirror_area=None,
            num_mirror_tiles=None,
        )

    @staticmethod
    def is_compatible(file_path):
        # just check if root file is given
        return file_path[-4:] == "root"

    def _generator(self):
        data = DataContainer()
        data.meta["origin"] = "magicio"

        # Get both data paths from single input_url
        # It is assumed that both files are in the same location
        # TODO: Get second input_url?
        # TODO: (Rewrite EventSource.__init__ to correctly use core.Provenance)
        if "_M1_" in self.input_url:
            path_I = self.input_url
            path_II = self.input_url.replace("_M1_", "_M2_")
        elif "_M2_" in self.input_url:
            path_II = self.input_url
            path_I = self.input_url.replace("_M2_", "_M1_")

        # open data with uproot
        magic_I = uproot.open(path_I)
        magic_II = uproot.open(path_II)

        # check if data file is monte carlo or data by checking keys
        if b"OriginalMC;1" in magic_I.keys():
            is_mc = True

        # Event data same in both files (mc / data)
        events = magic_I[b"Events"]
        fPhot_I = events[b"MCerPhotEvt.fPixels.fPhot"].array()
        # TODO: Get Pointing Positions for both telescopes
        Zd_I = events[b"MPointingPos.fDevZd"].array()
        Az_I = events[b"MPointingPos.fDevAz"].array()

        events = magic_II[b"Events"]
        fPhot_II = events[b"MCerPhotEvt.fPixels.fPhot"].array()
        # TODO: Get Pointing Positions for both telescopes
        Zd_II = events[b"MPointingPos.fDevZd"].array()
        Az_II = events[b"MPointingPos.fDevAz"].array()

        if is_mc:  # Monte Carlo
            # TODO: Fill MCEventContainer
            data.mc.energy = 0.0 * u.TeV
            data.mc.alt = 0.0 * u.deg
            data.mc.az = 0.0 * u.deg
            data.mc.core_x = 0.0 * u.m
            data.mc.core_y = 0.0 * u.m
            data.mc.h_first_int = 0.0
            data.mc.x_max = 0.0 * u.g / (u.cm ** 2)
            data.mc.shower_primary_id = 0

            # TODO: Fill InstrumentContainer (deprecated)
            data.inst.subarray = SubarrayDescription("MonteCarloArray")
            data.inst.subarray.tels = {
                0: TelescopeDescription(optics=self.optics, camera=self.camgeom),
                1: TelescopeDescription(optics=self.optics, camera=self.camgeom),
            }
            data.inst.subarray.tels[0].optics.equivalent_focal_length = 1 * u.km
            data.inst.subarray.tels[1].optics.equivalent_focal_length = 1 * u.km
            # TODO: Find out positions of telescopes
            data.inst.subarray.positions = {0: [0, 0, 0], 1: [10, 10, 0]}

            for i, (evt_I, evt_II) in enumerate(zip(fPhot_I, fPhot_II)):
                # Fill MCCameraEventContainer
                data.mc.tel[0].photo_electron_image = i
                data.mc.tel[1].photo_electron_image = i
                data.mc.tel[0].azimuth_raw = 0.0
                data.mc.tel[0].altitude_raw = 0.0
                data.mc.tel[1].azimuth_raw = 0.0
                data.mc.tel[1].altitude_raw = 0.0

                # Fill DL1Container (calibrated image)
                data.dl1.tel[0].image = evt_I[:1039]
                data.dl1.tel[0].peakpos = None
                data.dl1.tel[1].image = evt_II[:1039]
                data.dl1.tel[1].peakpos = None

                # TODO: Fill TelescopePointingContainer
                data.pointing[0].azimuth = Zd_I[i]
                data.pointing[0].altitude = Az_I[i]
                data.pointing[1].azimuth = Zd_II[i]
                data.pointing[1].altitude = Az_II[i]

                yield data

        else:  # Measurement, Real Data
            for evt_I, evt_II in zip(fPhot_I, fPhot_II):
                # Fill DL1Container (calibrated image)
                data.dl1.tel[0].image = evt_I[:1039]
                data.dl1.tel[0].peakpos = None
                data.dl1.tel[1].image = evt_II[:1039]
                data.dl1.tel[1].peakpos = None

                # TODO Fill TelescopePointingContainer
                data.pointing[0].azimuth = 0 * u.rad
                data.pointing[0].altitude = 0 * u.rad
                data.pointing[1].azimuth = 0 * u.rad
                data.pointing[1].altitude = 0 * u.rad
                yield data

        return

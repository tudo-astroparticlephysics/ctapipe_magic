import uproot

# import numpy as np
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

        # TODO: Initialize CameraGeometry and OpticsDescription
        # needed for subarray information in
        # data.inst.subarray (but is deprecated ??)
        self.camgeom = CameraGeometry.from_name(camera_id="MAGICCam")
        self.optics = OpticsDescription(
            mirror_type="SC",
            tel_type="MST",
            tel_subtype="1M",
            equivalent_focal_length=1700 * u.cm,
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
        #   (Rewrite EventSource.__init__ to correctly use core.Provenance)
        paths = {}
        if "_M1_" in self.input_url:
            paths[0] = self.input_url
            paths[1] = self.input_url.replace("_M1_", "_M2_")
        elif "_M2_" in self.input_url:
            paths[1] = self.input_url
            paths[0] = self.input_url.replace("_M1_", "_M2_")

        # open data with uproot
        magic_data = {0: uproot.open(paths[0]), 1: uproot.open(paths[1])}

        # check if data file is monte carlo or data by checking keys
        is_mc = b"OriginalMC;1" in magic_data[0].keys()

        # Event data same in both files (mc / data)
        events = {0: magic_data[0][b"Events"], 1: magic_data[1][b"Events"]}

        data.meta["n_events"] = min(len(events[0]), len(events[1]))

        fPhots = {
            0: events[0][b"MCerPhotEvt.fPixels.fPhot"].array(),
            1: events[1][b"MCerPhotEvt.fPixels.fPhot"].array(),
        }

        Az = {
            0: events[0][b"MPointingPos.fAz"].array(),
            1: events[1][b"MPointingPos.fAz"].array(),
        }

        Zd = {
            0: events[0][b"MPointingPos.fZd"].array(),
            1: events[1][b"MPointingPos.fZd"].array(),
        }

        if is_mc:  # Monte Carlo
            # Particle ID, mapping = {magic: ctapipe}
            particle_id_mapping = {1: 0}  # gamma
            # TODO: Fill InstrumentContainer (deprecated)
            data.inst.subarray = SubarrayDescription("MonteCarloArray")
            data.inst.subarray.tels = {
                0: TelescopeDescription(optics=self.optics, camera=self.camgeom),
                1: TelescopeDescription(optics=self.optics, camera=self.camgeom),
            }
            # TODO: Find out positions of telescopes
            data.inst.subarray.positions = {  # has to be in meters
                0: [31.80, -28.10, 0],  #  3180, -2810 cm
                1: [-31.80, 28.10, 0],  # -3180,  2810 cm
            }

            primary_id = events[0][b"MMcEvt.fPartId"].array()
            energy = events[0][b"MMcEvt.fEnergy"].array()
            core_x = events[0][b"MMcEvt.fCoreX"].array()
            core_y = events[0][b"MMcEvt.fCoreY"].array()
            zFirstInt = events[0][b"MMcEvt.fZFirstInteraction"].array()

            # Fill container per event
            for i in range(data.meta["n_events"]):
                data.mc.shower_primary_id = particle_id_mapping[primary_id[i]]

                # # TODO: Fill MCEventContainer
                data.mc.energy = energy[i] * u.MeV
                data.mc.core_x = core_x[i] * u.cm
                data.mc.core_y = core_y[i] * u.cm
                data.mc.h_first_int = (zFirstInt[i] * u.cm,)
                # data.mc.x_max = 0.0 * u.g / (u.cm ** 2)
                # IMPORTANT TODO: mc.alt mc.az
                data.mc.az = (Az[0][i] - 0.4) * u.deg
                data.mc.alt = (90.0 - Zd[0][i]) * u.deg
                # Fill MCCameraEventContainer
                data.mc.tel[0].photo_electron_image = i
                data.mc.tel[1].photo_electron_image = i

                # Fill DL1Container (calibrated image)
                data.dl1.tel[0].image = fPhots[0][i][:1039]
                data.dl1.tel[0].peakpos = None
                data.dl1.tel[1].image = fPhots[1][i][:1039]
                data.dl1.tel[1].peakpos = None

                # TODO: Fill TelescopePointingContainer
                data.pointing[0].azimuth = Az[0][i] * u.deg
                data.pointing[0].altitude = (90.0 - Zd[0][i]) * u.deg
                data.pointing[1].azimuth = Az[1][i] * u.deg
                data.pointing[1].altitude = (90.0 - Zd[1][i]) * u.deg

                yield data

        # TODO: REAL DATA
        else:  # Measurement, Real Data
            for evt_I, evt_II in zip(fPhots[0], fPhots[1]):
                # Fill DL1Container (calibrated image)
                data.dl1.tel[0].image = evt_I[:1039]
                data.dl1.tel[0].peakpos = None
                data.dl1.tel[1].image = evt_II[:1039]
                data.dl1.tel[1].peakpos = None

                # TODO Fill TelescopePointingContainer
                data.pointing[0].azimuth = Az[0][i] * u.deg
                data.pointing[0].altitude = (90 - Zd[0][i]) * u.deg
                data.pointing[1].azimuth = Az[1][i] * u.deg
                data.pointing[1].altitude = (90 - Zd[1][i]) * u.deg

                yield data

        return

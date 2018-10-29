import uproot
from ctapipe.io.eventsource import EventSource
from ctapipe.io.containers import DataContainer


__all__ = ["MAGICIOEventSource"]


class MAGICIOEventSource(EventSource):
    """
    EventSource for the magic file format.

    This class utilises `uproot` to read the magic files, and stores the
    information into the event containers.

    Install `uproot` using `pip`:
    `pip install uproot`
    """

    _count = 0

    def __init__(self, config=None, tool=None, **kwargs):
        super().__init__(config=config, tool=tool, **kwargs)

    @staticmethod
    def is_compatible(file_path):
        # just check if root file is given
        return file_path[-4:] == "root"

    def _generator(self):
        data = DataContainer()
        data.meta["origin"] = "magicio"

        # Get both data paths from single input_url
        # It is assumed, that both files are in the same location
        if "_M1_" in self.input_url:
            path_I = self.input_url
            path_II = self.input_url.replace("_M1_", "_M2_")
        elif "_M2_" in self.input_url:
            path_II = self.input_url
            path_I = self.input_url.replace("_M2_", "_M1_")

        # open data with uproot
        magic_I = uproot.open(path_I)
        magic_II = uproot.open(path_II)

        events = magic_I[b"Events"]
        fPhot_I = events[b"MCerPhotEvt.fPixels.fPhot"].array()

        events = magic_II[b"Events"]
        fPhot_II = events[b"MCerPhotEvt.fPixels.fPhot"].array()

        for evt_I, evt_II in zip(fPhot_I, fPhot_II):
            data.dl1.tel[0].image = evt_I[:1039]
            data.dl1.tel[0].peakpos = None

            data.dl1.tel[1].image = evt_II[:1039]
            data.dl1.tel[1].peakpos = None
            yield data
        return

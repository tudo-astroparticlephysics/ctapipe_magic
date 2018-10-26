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

        # open data with uproot
        magic_I = uproot.open(self.input_url)
        magic_II = uproot.open(self.input_url)

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

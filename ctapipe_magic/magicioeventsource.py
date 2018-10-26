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
        data = DL1Container()
        data_camera = DL1CameraContainer()
        data.meta["origin"] = "magicio"

        # open data with uproot
        opened = self.uproot.open(self.input_url)

        # # Maybe we don't need this, in one single file I tested there were
        # # two Events branches, with one longer than the other and
        # # containing everything the shorter one contained
        # # Sometimes there are more than 1 event branches in the root files
        # event_keys = []
        # for key in opened.keys():
        #     if b"Events" in key:
        #         event_keys.append(key)

        # --- Implement Logic here ---
        # todo:
        # - extract metadata from files
        # - get two files for two magic telescopes
        # - input every event from file into correspondig container

        events = opened[b"Events"]
        fPhot_arr = events[b"MCerPhotEvt.fPixels.fPhot"].array()

        for evt in fPhot_arr:
            data_camera.image = evt[:1039]
            data_camera.peakpos = None
            data.tel = data_camera
            yield data
        return

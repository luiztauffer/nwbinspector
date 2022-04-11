"""Helper functions for internal use that rely on external dependencies (i.e., pynwb)."""
from uuid import uuid4
from datetime import datetime

from pynwb import NWBFile


def make_minimal_nwbfile():
    """Most basic NWBFile that can exist."""
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())


def all_of_type(nwbfile: NWBFile, neurodata_type):
    """Iterate over all objects inside an NWBFile object and return those that match the given neurodata_type."""
    for obj in nwbfile.objects.values():
        if isinstance(obj, neurodata_type):
            yield obj


def get_nwbfile_path_from_internal_object(obj):
    """Determine the file path on disk for a NWBFile given only an internal object of that file."""
    if isinstance(obj, NWBFile):
        return obj.container_source
    return obj.get_ancestor("NWBFile").container_source

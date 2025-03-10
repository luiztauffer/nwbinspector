"""Check functions specific to extracellular electrophysiology neurodata types."""
import numpy as np

from pynwb.misc import Units
from pynwb.ecephys import ElectricalSeries

from ..utils import get_data_shape

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_negative_spike_times(units_table: Units):
    """Check if the Units table contains negative spike times."""
    if "spike_times" not in units_table:
        return
    if np.any(np.asarray(units_table["spike_times"].target.data[:]) < 0):
        return InspectorMessage(
            message=(
                "This Units table contains negative spike times. Time should generally be aligned to the earliest "
                "time reference in the NWBFile."
            )
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=ElectricalSeries)
def check_electrical_series_dims(electrical_series: ElectricalSeries):
    """
    Use the length of the linked electrode region to check the data orientation.

    Best Practice: :ref:`best_practice_data_orientation`
    """
    data = electrical_series.data
    electrodes = electrical_series.electrodes

    data_shape = get_data_shape(data, strict_no_data_load=True)
    if data_shape and len(data_shape) == 2 and data_shape[1] != len(electrodes.data):
        if data_shape[0] == len(electrodes.data):
            return InspectorMessage(
                message=(
                    "The second dimension of data does not match the length of electrodes, "
                    "but instead the first does. Data is oriented incorrectly and should be transposed."
                )
            )
        return InspectorMessage(
            message=(
                "The second dimension of data does not match the length of electrodes. Your " "data may be transposed."
            )
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ElectricalSeries)
def check_electrical_series_reference_electrodes_table(electrical_series: ElectricalSeries):
    """Check that the 'electrodes' of an ElectricalSeries references the ElectrodesTable."""
    if electrical_series.electrodes.table.name != "electrodes":
        return InspectorMessage(message="electrodes does not  reference an electrodes table.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_spike_times_not_in_unobserved_interval(units_table: Units, nunits: int = 4):
    """Check if a Units table has spike times that occur outside of observed intervals."""
    if not units_table.obs_intervals:
        return
    for unit_spike_times, unit_obs_intervals in zip(
        units_table["spike_times"][:nunits], units_table["obs_intervals"][:nunits]
    ):
        spike_times_array = np.array(unit_spike_times)
        if not all(
            sum(
                [
                    np.logical_and(start <= spike_times_array, spike_times_array <= stop)
                    for start, stop in unit_obs_intervals
                ]
            )
        ):
            return InspectorMessage(
                message=(
                    "This Units table contains spike times that occur during periods of time not labeled as being "
                    "observed intervals."
                )
            )

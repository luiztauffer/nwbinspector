"""Check functions that can apply to any descendant of TimeSeries."""
import numpy as np

from pynwb import TimeSeries
from pynwb.image import ImageSeries, IndexSeries

from ..register_checks import register_check, Importance, Severity, InspectorMessage
from ..utils import is_regular_series, is_ascending_series, get_data_shape


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_regular_timestamps(
    time_series: TimeSeries, time_tolerance_decimals: int = 9, gb_severity_threshold: float = 1.0
):
    """If the TimeSeries uses timestamps, check if they are regular (i.e., they have a constant rate)."""
    if (
        time_series.timestamps is not None
        and len(time_series.timestamps) > 2
        and is_regular_series(series=time_series.timestamps, tolerance_decimals=time_tolerance_decimals)
    ):
        timestamps = np.array(time_series.timestamps)
        if timestamps.size * timestamps.dtype.itemsize > gb_severity_threshold * 1e9:
            severity = Severity.HIGH
        else:
            severity = Severity.LOW
        return InspectorMessage(
            severity=severity,
            message=(
                "TimeSeries appears to have a constant sampling rate. "
                f"Consider specifying starting_time={time_series.timestamps[0]} "
                f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
            ),
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_data_orientation(time_series: TimeSeries):
    """If the TimeSeries has data, check if the longest axis (almost always time) is also the zero-axis."""
    if time_series.data is None:
        return

    data_shape = get_data_shape(time_series.data)
    if any(np.array(data_shape[1:]) > data_shape[0]):
        return InspectorMessage(
            message=(
                "Data may be in the wrong orientation. Time should be in the first dimension, and is usually the "
                "longest dimension. Here, another dimension is longer."
            ),
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_timestamps_match_first_dimension(time_series: TimeSeries):
    """
    If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data.

    Best Practice: :ref:`best_practice_data_orientation`
    """
    if time_series.data is None or time_series.timestamps is None:
        return

    if getattr(time_series, "external_file", None) is not None and get_data_shape(time_series.data)[0] == 0:
        return

    # A very specific edge case where this has been allowed, though much more preferable
    # to use a stack of Images rather than an ImageSeries
    if (
        isinstance(time_series, ImageSeries)
        and len(time_series.timestamps) == 0
        and time_series.get_ancestor("NWBFile") is not None
    ):
        for neurodata_object in time_series.get_ancestor("NWBFile").objects.values():
            if isinstance(neurodata_object, IndexSeries) and neurodata_object.indexed_timeseries == time_series:
                return

    timestamps_shape = get_data_shape(time_series.timestamps)
    data_shape = get_data_shape(time_series.data)
    if data_shape[0] != timestamps_shape[0]:
        return InspectorMessage(
            message=(
                f"The length of the first dimension of data ({data_shape[0]}) "
                f"does not match the length of timestamps ({timestamps_shape[0]})."
            )
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_timestamps_ascending(time_series: TimeSeries, nelems=200):
    """Check that the values in the timestamps array are strictly increasing."""
    if time_series.timestamps is not None and not is_ascending_series(time_series.timestamps, nelems=nelems):
        return InspectorMessage(f"{time_series.name} timestamps are not ascending.")


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=TimeSeries)
def check_timestamp_of_the_first_sample_is_not_negative(time_series: TimeSeries):
    """
    Check that the timestamp of the first sample is not negative.

    Best Practice: :ref:`best_practice_global_time_reference`
    """

    first_timestamp = time_series.starting_time if time_series.starting_time is not None else time_series.timestamps[0]
    if first_timestamp < 0:
        return InspectorMessage(
            message="Timestamps should not be negative."
            " It is recommended to align the `session_start_time` or `timestamps_reference_time` to be the earliest time value that occurs in the data, and shift all other signals accordingly."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_missing_unit(time_series: TimeSeries):
    """
    Check if the TimeSeries.unit field is empty.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if not time_series.unit:
        return InspectorMessage(
            message="Missing text for attribute 'unit'. Please specify the scientific unit of the 'data'."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_resolution(time_series: TimeSeries):
    """Check the resolution value of a TimeSeries for proper format (-1.0 or NaN for unknown)."""
    if time_series.resolution is None or time_series.resolution == -1.0:
        return
    if time_series.resolution <= 0:
        return InspectorMessage(
            message=f"'resolution' should use -1.0 or NaN for unknown instead of {time_series.resolution}."
        )

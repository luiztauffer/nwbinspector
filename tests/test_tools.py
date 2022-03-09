import numpy as np
from uuid import uuid4
from datetime import datetime

import pynwb
from hdmf.testing import TestCase

from nwbinspector.tools import all_of_type
from nwbinspector.inspector_tools import organize_messages
from nwbinspector.register_checks import InspectorMessage, Importance, Severity


def test_all_of_type():
    nwbfile = pynwb.NWBFile(
        session_description="Testing inspector.",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    true_time_series = [
        pynwb.TimeSeries(name=f"time_series_{x}", data=np.zeros(shape=(100, 10)), rate=1.0, unit="") for x in range(4)
    ]
    for x in range(2):
        nwbfile.add_acquisition(true_time_series[x])
    ecephys_module = nwbfile.create_processing_module(name="ecephys", description="")
    ecephys_module.add(true_time_series[2])
    ophys_module = nwbfile.create_processing_module(name="ophys", description="")
    ophys_module.add(true_time_series[3])

    nwbfile_time_series = [obj for obj in all_of_type(nwbfile=nwbfile, neurodata_type=pynwb.TimeSeries)]
    for time_series in true_time_series:
        assert time_series in nwbfile_time_series


class TestOrganization(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.messages = [
            InspectorMessage(
                message="test1",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="fun1",
                object_type="ElectricalSeries",
                object_name="ts1",
                location="/acquisition/",
                file="file1.nwb",
            ),
            InspectorMessage(
                message="test2",
                importance=Importance.CRITICAL,
                check_function_name="fun2",
                object_type="DynamicTable",
                object_name="tab",
                location="/acquisition/",
                file="file1.nwb",
            ),
            InspectorMessage(
                message="test3",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                severity=Severity.HIGH,
                check_function_name="fun3",
                object_type="NWBFile",
                object_name="root",
                location="/",
                file="file2.nwb",
            ),
            InspectorMessage(
                message="test4",
                importance=Importance.CRITICAL,
                check_function_name="fun2",
                object_type="ElectricalSeries",
                object_name="ts1",
                location="/processing/ecephys/LFP/",
                file="file3.nwb",
            ),
        ]

    def test_message_level_assertion(self):
        with self.assertRaisesWith(
            exc_type=AssertionError,
            exc_msg=(
                "You must specify levels to organize by that correspond to attributes of the InspectorMessage class, "
                "not including the text message."
            ),
        ):
            organize_messages(messages=self.messages, levels=["message"])

    def test_file_by_importance(self):
        test_result = organize_messages(messages=self.messages, levels=["file", "importance"])
        true_result = {
            "file1.nwb": {
                Importance.CRITICAL: [
                    InspectorMessage(
                        message="test2",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="DynamicTable",
                        object_name="tab",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ],
                Importance.BEST_PRACTICE_SUGGESTION: [
                    InspectorMessage(
                        message="test1",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.LOW,
                        check_function_name="fun1",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ],
            },
            "file2.nwb": {
                Importance.BEST_PRACTICE_SUGGESTION: [
                    InspectorMessage(
                        message="test3",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.HIGH,
                        check_function_name="fun3",
                        object_type="NWBFile",
                        object_name="root",
                        location="/",
                        file="file2.nwb",
                    )
                ]
            },
            "file3.nwb": {
                Importance.CRITICAL: [
                    InspectorMessage(
                        message="test4",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/processing/ecephys/LFP/",
                        file="file3.nwb",
                    )
                ]
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)

    def test_severity_by_object_type_by_location(self):
        test_result = organize_messages(messages=self.messages, levels=["severity", "object_type", "location"])
        true_result = {
            Severity.HIGH: {
                "NWBFile": {
                    "/": [
                        InspectorMessage(
                            message="test3",
                            importance=Importance.BEST_PRACTICE_SUGGESTION,
                            severity=Severity.HIGH,
                            check_function_name="fun3",
                            object_type="NWBFile",
                            object_name="root",
                            location="/",
                            file="file2.nwb",
                        )
                    ]
                }
            },
            Severity.LOW: {
                "DynamicTable": {
                    "/acquisition/": [
                        InspectorMessage(
                            message="test2",
                            importance=Importance.CRITICAL,
                            severity=Severity.LOW,
                            check_function_name="fun2",
                            object_type="DynamicTable",
                            object_name="tab",
                            location="/acquisition/",
                            file="file1.nwb",
                        )
                    ]
                },
                "ElectricalSeries": {
                    "/acquisition/": [
                        InspectorMessage(
                            message="test1",
                            importance=Importance.BEST_PRACTICE_SUGGESTION,
                            severity=Severity.LOW,
                            check_function_name="fun1",
                            object_type="ElectricalSeries",
                            object_name="ts1",
                            location="/acquisition/",
                            file="file1.nwb",
                        )
                    ],
                    "/processing/ecephys/LFP/": [
                        InspectorMessage(
                            message="test4",
                            importance=Importance.CRITICAL,
                            severity=Severity.LOW,
                            check_function_name="fun2",
                            object_type="ElectricalSeries",
                            object_name="ts1",
                            location="/processing/ecephys/LFP/",
                            file="file3.nwb",
                        )
                    ],
                },
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)

    def test_check_function_name_by_object_name(self):
        test_result = organize_messages(messages=self.messages, levels=["check_function_name", "object_name"])
        true_result = {
            "fun1": {
                "ts1": [
                    InspectorMessage(
                        message="test1",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.LOW,
                        check_function_name="fun1",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ]
            },
            "fun2": {
                "tab": [
                    InspectorMessage(
                        message="test2",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="DynamicTable",
                        object_name="tab",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ],
                "ts1": [
                    InspectorMessage(
                        message="test4",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/processing/ecephys/LFP/",
                        file="file3.nwb",
                    )
                ],
            },
            "fun3": {
                "root": [
                    InspectorMessage(
                        message="test3",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.HIGH,
                        check_function_name="fun3",
                        object_type="NWBFile",
                        object_name="root",
                        location="/",
                        file="file2.nwb",
                    )
                ]
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)

    def test_reverse(self):
        test_result = organize_messages(messages=self.messages, levels=["importance", "file"], reverse=[False, True])
        true_result = {
            Importance.CRITICAL: {
                "file3.nwb": [
                    InspectorMessage(
                        message="test4",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/processing/ecephys/LFP/",
                        file="file3.nwb",
                    )
                ],
                "file1.nwb": [
                    InspectorMessage(
                        message="test2",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="DynamicTable",
                        object_name="tab",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ],
            },
            Importance.BEST_PRACTICE_SUGGESTION: {
                "file2.nwb": [
                    InspectorMessage(
                        message="test3",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.HIGH,
                        check_function_name="fun3",
                        object_type="NWBFile",
                        object_name="root",
                        location="/",
                        file="file2.nwb",
                    )
                ],
                "file1.nwb": [
                    InspectorMessage(
                        message="test1",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.LOW,
                        check_function_name="fun1",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/acquisition/",
                        file="file1.nwb",
                    )
                ],
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)

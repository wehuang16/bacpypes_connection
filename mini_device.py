#!/usr/bin/python

"""
This sample application is a server that supports many core services that
applications need to present data on a BACnet network.  It supports Who-Is
and I-Am for device binding, Read and Write Property, Read and Write
Property Multiple, and COV subscriptions.

Change the process_task() function to do something on a regular INTERVAL
number of seconds.
"""
"""
        weeklySchedule=DailySchedule(
                daySchedule=[
                    TimeValue(time=(8, 0, 0, 0), value=Real(8.0)),
                    TimeValue(time=(14, 0, 0, 0), value=Null()),
                    TimeValue(time=(17, 0, 0, 0), value=Real(42.0)),
                ]
            ),
"""
from time import localtime as _localtime
from pandas import *
import numpy as np
from matplotlib.pyplot import *

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run
from bacpypes.task import RecurringTask

from bacpypes.primitivedata import Null, Real, Date, Time, Integer, Unsigned8, Unsigned, Enumerated,Boolean,BitString
from bacpypes.constructeddata import ArrayOf, ListOf
from bacpypes.basetypes import (
    CalendarEntry,
    DailySchedule,
    DateRange,
    DeviceObjectPropertyReference,
    SpecialEvent,
    SpecialEventPeriod,
    TimeValue,
)

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import (AnalogValueObject, 
    BinaryValueObject, 
    register_object_type, 
    WritableProperty, 
    AnalogValueObject,
    PositiveIntegerValueObject,
    MultiStateValueObject,
    IntegerValueObject,
    ScheduleObject
)

from bacpypes.local.device import LocalDeviceObject
from bacpypes.local.object import CurrentPropertyListMixIn
from bacpypes.local.schedule import LocalScheduleObject
from bacpypes.service.cov import ChangeOfValueServices
from bacpypes.service.object import ReadWritePropertyMultipleServices

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
INTERVAL = 1.0

# globals
test_application = None
test_av = None
test_bv = None
test_msv = None
test_iv = None


@bacpypes_debugging
class SampleApplication(
    BIPSimpleApplication, ReadWritePropertyMultipleServices, ChangeOfValueServices
):
    pass


@bacpypes_debugging
class DoSomething(RecurringTask):
    def __init__(self, interval):
        if _debug:
            DoSomething._debug("__init__ %r", interval)
        RecurringTask.__init__(self, interval * 1000)

        # save the interval
        self.interval = interval

        # make a list of test values
        self.test_values = [
            ("active", 1.0),
            ("inactive", 2.0),
            ("active", 3.0),
            ("inactive", 4.0),
        ]

    def process_task(self):
        if _debug:
            DoSomething._debug("process_task")
        global test_av, test_bv, test_msv, test_iv

        # pop the next value
        next_value = self.test_values.pop(0)
        self.test_values.append(next_value)
        if _debug:
            DoSomething._debug("    - next_value: %r", next_value)

        # change the point
        #test_msv.presentValue = next_value[2]
        test_av.presentValue = next_value[1]
        test_bv.presentValue = next_value[0]


def main():
    global test_av, test_bv, test_msv, test_iv, test_application

    # make a parser
    parser = ConfigArgumentParser(description=__doc__)

    # parse the command line arguments
    args = parser.parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a sample application
    test_application = SampleApplication(this_device, args.ini.address)

    # make an analog value object
    test_av = AnalogValueObject(
        objectIdentifier=("analogValue", 1),
        objectName="av",
        presentValue=0.0,
        statusFlags=[0],
        covIncrement=1.0,
        deadband=3.0,
        lowLimit=6.0,
    )
    _log.debug("    - test_av: %r", test_av)

    # add it to the device
    test_application.add_object(test_av)
    _log.debug("    - object list: %r", this_device.objectList)

    # make an positive value object
    test_msv = MultiStateValueObject(
        objectIdentifier=("multiStateValue", 1),
        objectName="msv",
        presentValue=Unsigned(4),
        statusFlags=[0],
        outOfService=Boolean(True),
        numberOfStates=Unsigned(1),
    )
    _log.debug("    - test_msv: %r", test_msv)

    # add it to the device
    test_application.add_object(test_msv)
    _log.debug("    - object list: %r", this_device.objectList)


    # make an positive value object
    test_iv = IntegerValueObject(
        objectIdentifier=("integerValue", 1),
        objectName="iv",
        presentValue=Integer(7),
        statusFlags=[0],
        outOfService=Boolean(False),
        minPresValue=Integer(2),
    )
    _log.debug("    - test_iv: %r", test_iv)

    # add it to the device
    test_application.add_object(test_iv)
    _log.debug("    - object list: %r", this_device.objectList)


    # make a binary value object
    test_bv = BinaryValueObject(
        objectIdentifier=("binaryValue", 1),
        objectName="bv",
        presentValue="inactive",
        statusFlags=[0],
        outOfService=Boolean(False)
    )
    _log.debug("    - test_bv: %r", test_bv)

    # add it to the device
    test_application.add_object(test_bv)

    # binary value task
    do_something_task = DoSomething(INTERVAL)
    do_something_task.install_task()

    # make a schedule object
    test_schedule = ScheduleObject(
        objectIdentifier=("schedule", 1),
        objectName="Test Schedule",
        presentValue=Unsigned(2),
        statusFlags=[0,0,0,1],
        effectivePeriod=DateRange(startDate=(0, 1, 1, 1), endDate=(254, 12, 31, 2)),
        
        weeklySchedule=ArrayOf(DailySchedule, 7)([
            DailySchedule(
                daySchedule=[
                    TimeValue(time=(0, 0, 0, 0), value=Unsigned(1)),
                    TimeValue(time=(5, 0, 0, 0), value=Unsigned(2)),
                    TimeValue(time=(12, 0, 0, 0), value=Unsigned(1)),
                    TimeValue(time=(13, 0, 0, 0), value=Unsigned(2)),
                    TimeValue(time=(20, 0, 0, 0), value=Unsigned(1)),
                ]
            )
        ]
        * 7),
        scheduleDefault=Unsigned(1),
        exceptionSchedule=None,
    )

    # add it to the device
    test_application.add_object(test_schedule)

    _log.debug("running")

    run()

    _log.debug("fini")
"""

        listOfObjectPropertyReferences=ListOf(DeviceObjectPropertyReference)(
            [
                DeviceObjectPropertyReference(
                    objectIdentifier=("positiveIntegerValue", 1),
                    propertyIdentifier="presentValue",
                )
            ]
        ),
"""

if __name__ == "__main__":
    main()

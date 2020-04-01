#!/usr/bin/env python3

from pconfig import ConfigManager, ConfigAttrDetails
from uio import UIO

def example1():#
    """@brief This example uses a high level interface to populate the config dict."""
    uio = UIO()

    LOW_CHARGE_BAT_VOLTAGE_FLOAT        =   "LOW_CHARGE_BAT_VOLTAGE_FLOAT"
    FULL_CHARGE_BAT_VOLTAGE_FLOAT       =   "FULL_CHARGE_BAT_VOLTAGE_FLOAT"
    MAX_CURRENT_AMPS_INT                =   "MAX_CURRENT_AMPS_INT"
    A_STRING_VALUE_STR                  =   "A_STRING_VALUE_STR"
    THE_ADDRESS_HEXINT                  =   "THE_ADDRESS_HEXINT"

    defaultConfig = {
        LOW_CHARGE_BAT_VOLTAGE_FLOAT:   12.2,
        FULL_CHARGE_BAT_VOLTAGE_FLOAT:  13.5,
        MAX_CURRENT_AMPS_INT:           1000,
        A_STRING_VALUE_STR:             "ANYSTRING",
        THE_ADDRESS_HEXINT:             0x1234
    }

    configAttrDetailsDict = {
        LOW_CHARGE_BAT_VOLTAGE_FLOAT:   ConfigAttrDetails("Enter the low charge battery voltage", 10.0, 15.0),
        FULL_CHARGE_BAT_VOLTAGE_FLOAT:  ConfigAttrDetails("Enter the battery full charge voltage", 10, 15),
        MAX_CURRENT_AMPS_INT:           ConfigAttrDetails("Enter the max amps"),
        A_STRING_VALUE_STR:             ConfigAttrDetails("Enter a string", allowEmpty=True),
        THE_ADDRESS_HEXINT:             ConfigAttrDetails("Enter the address (hex)")
        }

    configManager = ConfigManager(uio, "example_1_config.txt", defaultConfig)
    configManager.edit(configAttrDetailsDict)

def example2():
    """@brief This example uses a lower level interface that allows more control of the user interface.."""
    uio = UIO()

    LOW_CHARGE_BAT_VOLTAGE="LOW_CHARGE_BAT_VOLTAGE"
    FULL_CHARGE_BAT_VOLTAGE="FULL_CHARGE_BAT_VOLTAGE"
    MAX_CURRENT_AMPS="MAX_CURRENT_AMPS"
    A_STRING_VALUE="A_STRING_VALUE"
    THE_ADDRESS="THE_ADDRESS"

    defaultConfig = {
        LOW_CHARGE_BAT_VOLTAGE: 12.2,
        FULL_CHARGE_BAT_VOLTAGE: 13.5,
        MAX_CURRENT_AMPS: 1000,
        A_STRING_VALUE: "ANYSTRING",
        THE_ADDRESS: 0x1234
    }

    configManager = ConfigManager(uio, "example_2_config.txt", defaultConfig)

    lowBatVoltage = ConfigManager.GetFloat(uio, "Enter the low charge battery voltage", minValue=10.0,
                                           maxValue=15.0)
    configManager.addAttr(LOW_CHARGE_BAT_VOLTAGE, lowBatVoltage)

    fullBatVoltage = ConfigManager.GetFloat(uio, "Enter the battery full charge voltage",
                                            minValue=lowBatVoltage, maxValue=15.0)
    configManager.addAttr(FULL_CHARGE_BAT_VOLTAGE, fullBatVoltage)

    configManager.inputFloat(MAX_CURRENT_AMPS, "Enter the max amps")

    configManager.inputStr(A_STRING_VALUE, "Enter a string", allowEmpty=False)

    configManager.inputHexInt(THE_ADDRESS, "Enter the address (hex)",
                                            minValue=0x1000, maxValue=0x2000)

    configManager.store()

if __name__ == '__main__':
    example1()
    #example2()

#
# Copyright (C) 2025 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import time
import datetime as mainDate
from datetime import datetime

from freppledb.forecast.tests.seleniumpages.forecastlocators import (
    ForecastTableLocators,
)
from freppledb.common.tests.frepplePages.frepplepage import TablePage

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class ForecastTablePage(TablePage):
    def get_all_forecast_override_inputs_elements(self):
        all_forecast_input_cells = self.driver.find_elements(
            *ForecastTableLocators.FORECAST_OVERRIDE_CELLS
        )
        return all_forecast_input_cells

    def get_time_range(self):
        return len(self.get_all_forecast_override_inputs_elements())

    def get_value_target_override_cell(self, cellnumber):
        cellvalue = self.get_all_forecast_override_inputs_elements()[
            cellnumber - 1
        ].get_attribute("value")
        return cellvalue

    def set_value_target_override_cell(self, cellnumber, newvalue):
        targetcell = self.get_all_forecast_override_inputs_elements()[cellnumber - 1]

        targetcell.clear()
        time.sleep(0.3)
        targetcell.send_keys(newvalue)
        time.sleep(0.3)
        targetcell.send_keys(Keys.RETURN)
        time.sleep(0.3)

    def get_startdate_input(self):
        inputfield = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_STARTDATE
        )
        return inputfield

    def get_enddate_input(self):
        inputfield = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_ENDDATE
        )
        return inputfield

    def update_forecast_override_time_range(
        self, inputfield, monthsadded, overridevalue
    ):
        input_field = inputfield.get_attribute("id")

        def newdategenerator(olddate, monthsadded):
            old = datetime.strptime(olddate, "%Y-%m-%d")

            new = (
                old + mainDate.timedelta(days=(monthsadded * 31))
                if "start" in input_field
                else old - mainDate.timedelta(days=(monthsadded * 31))
            )

            return new

        timerange = 0

        oldany = inputfield.get_attribute("value")

        fromnewdate, tonewdate = None, None

        if "start" in input_field:
            tonewdate = newdategenerator(oldany, monthsadded)
            fromnewdate = datetime.strptime(
                self.get_startdate_input().get_attribute("value"), "%Y-%m-%d"
            )

            daterange = tonewdate - fromnewdate
            timerange = round(daterange.days / 30) + 1
            self.enter_text_in_inputdatefield(
                self.get_enddate_input(), tonewdate, withTime=False
            )
        else:
            fromnewdate = newdategenerator(oldany, monthsadded)
            tonewdate = datetime.strptime(
                self.get_enddate_input().get_attribute("value"), "%Y-%m-%d"
            )

            daterange = tonewdate - fromnewdate
            timerange = round(daterange.days / 30) + 1
            self.enter_text_in_inputdatefield(
                self.get_startdate_input(), fromnewdate, withTime=False
            )
            self.enter_text_in_inputdatefield(
                self.get_enddate_input(), tonewdate, withTime=False
            )

        override_input = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_SET_INPUT
        )

        self.enter_text_in_inputfield(override_input, overridevalue)
        return (fromnewdate, tonewdate, timerange)

    def enter_text_in_forecast_inputdatefield(self, targetinputdatefield, newdate):
        targetinputdatefield.clear()
        time.sleep(0.3)
        # when a simple clear of forecast enddate is not enough
        if len(targetinputdatefield.get_attribute("value")) > 0:
            for i in range(len(targetinputdatefield.get_attribute("value"))):
                targetinputdatefield.send_keys(Keys.BACKSPACE)

        targetinputdatefield.send_keys(newdate.strftime("%Y-%m-%d 00:00:00"))
        time.sleep(0.3)
        targetinputdatefield.send_keys(Keys.RETURN)
        time.sleep(0.3)
        return newdate.strftime("%Y-%m-%d 00:00:00")

    def click_apply_override_forecast_edit_button(self):
        apply_button = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_EDIT_APPLY_BUTTON
        )
        ActionChains(self.driver).move_to_element(apply_button).click().perform()

    def click_save_forecast(self):
        save_button = self.driver.find_element(*ForecastTableLocators.TABLE_SAVE_BUTTON)
        ActionChains(self.driver).move_to_element(save_button).click().perform()

    def click_undo_forecast(self):
        undo_button = self.driver.find_element(*ForecastTableLocators.TABLE_UNDO_BUTTON)
        ActionChains(self.driver).move_to_element(undo_button).click().perform()

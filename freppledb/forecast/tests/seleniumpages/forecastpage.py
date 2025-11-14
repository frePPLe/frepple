#
# Copyright (C) 2023 by frePPLe bv
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
from selenium.webdriver.common.by import By


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
            try:
                if not olddate or olddate.strip() == '':
                    old = datetime.now()
                else:
                    # Try parsing with time
                    try:
                        old = datetime.strptime(olddate, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            old = datetime.strptime(olddate, "%Y-%m-%d")
                        except ValueError:
                            old = datetime.now()
            except ValueError as e:
                old = datetime.now()

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

            # Get startdate value and handle empty case
            startdate_value = self.get_startdate_input().get_attribute("value")
            try:
                if not startdate_value or startdate_value.strip() == '':
                    fromnewdate = datetime.now()
                else:
                    try:
                        fromnewdate = datetime.strptime(startdate_value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            fromnewdate = datetime.strptime(startdate_value, "%Y-%m-%d")
                        except ValueError:
                            print(f"Warning: Could not parse start date '{startdate_value}', using current date")
                            fromnewdate = datetime.now()
            except Exception as e:
                fromnewdate = datetime.now()

            daterange = tonewdate - fromnewdate
            timerange = round(daterange.days / 30) + 1
            self.enter_text_in_forecast_inputdatefield(
                self.get_enddate_input(), tonewdate
            )
        else:
            fromnewdate = newdategenerator(oldany, monthsadded)

            # Get enddate value and handle empty case
            enddate_value = self.get_enddate_input().get_attribute("value")
            try:
                if not enddate_value or enddate_value.strip() == '':
                    tonewdate = datetime.now()
                else:
                    try:
                        tonewdate = datetime.strptime(enddate_value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            tonewdate = datetime.strptime(enddate_value, "%Y-%m-%d")
                        except ValueError:
                            print(f"Warning: Could not parse end date '{enddate_value}', using current date")
                            tonewdate = datetime.now()
            except Exception as e:
                print(f"Error parsing end date: {e}")
                tonewdate = datetime.now()

            daterange = tonewdate - fromnewdate
            timerange = round(daterange.days / 30) + 1
            self.enter_text_in_forecast_inputdatefield(
                self.get_startdate_input(), fromnewdate
            )
            self.enter_text_in_forecast_inputdatefield(
                self.get_enddate_input(), tonewdate
            )

        override_input = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_SET_INPUT
        )

        # Use JavaScript to set value and trigger Vue's @input event
        self.driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            """,
            override_input,
            overridevalue,
        )
        time.sleep(0.5)  # Give Vue's debounced input time to fire
        return (fromnewdate, tonewdate, timerange)

    def enter_text_in_forecast_inputdatefield(self, targetinputdatefield, newdate):
        # Format the date string to YYYY-MM-DD
        date_str = newdate.strftime("%Y-%m-%d")

        # Use JavaScript to set the value and trigger Vue events
        # This is far more reliable for <input type="date"> than send_keys
        self.driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
            targetinputdatefield,
            date_str,
        )
        time.sleep(0.5)  # Give Vue time to react
        return date_str

    def click_apply_override_forecast_edit_button(self):
        print("\n=== DEBUGGING FORM STATE (DETAILED) ===")

        # Find all radio buttons and their labels
        all_radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        print(f"Found {len(all_radios)} radio buttons:")
        for i, radio in enumerate(all_radios):
            name = radio.get_attribute("name")
            value = radio.get_attribute("value")
            checked = radio.is_selected()
            # Find associated label
            radio_id = radio.get_attribute("id")
            label_text = ""
            try:
                if radio_id:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                    label_text = label.text
            except:
                pass
            print(f"  {i}: name='{name}', value='{value}', checked={checked}, label='{label_text}'")

        # Find all visible text on the form (to see what options exist)
        form_container = self.driver.find_element(By.CSS_SELECTOR, "[class*='modal'], [class*='card'], form")
        print(f"\nForm text content (first 500 chars):")
        print(form_container.text[:500])

        # Look for any buttons or option groups
        all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
        print(f"\nFound {len(all_buttons)} buttons:")
        for i, btn in enumerate(all_buttons[:10]):
            text = btn.text or btn.get_attribute("title") or "(no text)"
            enabled = btn.is_enabled()
            print(f"  {i}: '{text}', enabled={enabled}")

        # Check page source for measure-related content
        page_source = self.driver.page_source
        import re
        # Find all text mentioning 'set', 'increase', 'measure'
        matches = re.findall(r'(set|increase|measure|select)[\w\s"\']*', page_source.lower())
        print(f"\nFound keywords in page source: {set(matches[:10])}")

        print("\n=== END DETAILED DEBUGGING ===\n")

        # Debug: Check UI state BEFORE clicking apply
        print("\n=== UI State BEFORE Apply Button ===")
        start_before = self.get_startdate_input().get_attribute("value")
        end_before = self.get_enddate_input().get_attribute("value")
        override_before = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_SET_INPUT
        ).get_attribute("value")
        print(f"Start date: {start_before}")
        print(f"End date: {end_before}")
        print(f"Override value: {override_before}")
        print()

        apply_button = self.driver.find_element(
            *ForecastTableLocators().FORECAST_OVERRIDE_EDIT_APPLY_BUTTON
        )

        print(f"Apply button enabled: {apply_button.is_enabled()}, visible: {apply_button.is_displayed()}")

        # Scroll button into view before clicking
        self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
        time.sleep(0.5)

        ActionChains(self.driver).move_to_element(apply_button).click().perform()
        time.sleep(1)

        # Don't try to access form elements after clicking Apply - they may have been re-rendered
        print("Apply button clicked successfully")

    def click_save_forecast(self):
        save_button = self.driver.find_element(*ForecastTableLocators.TABLE_SAVE_BUTTON)
        ActionChains(self.driver).move_to_element(save_button).click().perform()

    def click_undo_forecast(self):
        undo_button = self.driver.find_element(*ForecastTableLocators.TABLE_UNDO_BUTTON)
        ActionChains(self.driver).move_to_element(undo_button).click().perform()

    def select_measure_from_dropdown(self):
        """Select the first available measure from the dropdown to enable the Apply button."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Find the dropdown button (id="editmeasure")
        dropdown_btn = self.driver.find_element(By.CSS_SELECTOR, "button[id='editmeasure']")

        # Click to open the dropdown
        self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_btn)
        time.sleep(0.3)
        ActionChains(self.driver).move_to_element(dropdown_btn).click().perform()
        time.sleep(0.8)

        # Wait for dropdown items to be visible
        try:
            dropdown_items = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.dropdown-menu a.dropdown-item"))
            )
        except:
            # Try alternative selector
            dropdown_items = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu .dropdown-item, .dropdown-menu a")

        if len(dropdown_items) > 0:
            # Filter out empty items (which appear in your test log)
            filtered_dropdown_items = list(filter(lambda x: x.text.strip() != '', dropdown_items))
            print(f"Dropdown items found: {[item.text for item in dropdown_items]}")

            if not filtered_dropdown_items:
                raise Exception("Dropdown items were found, but all were empty.")

            # Get the text BEFORE clicking (to avoid stale element reference)
            first_item_text = filtered_dropdown_items[0].text

            # Scroll first item into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", filtered_dropdown_items[0])
            time.sleep(0.3)

            # Click the first *filtered* measure in the dropdown
            try:
                ActionChains(self.driver).move_to_element(filtered_dropdown_items[0]).click().perform()
            except:
                # Fallback: use JavaScript click
                self.driver.execute_script("arguments[0].click();", filtered_dropdown_items[0])

                time.sleep(0.5)
                print(f"Selected measure: {first_item_text} ")
        else:
            # Debug: show what's on the page
            print("ERROR: No dropdown items found")
            print(f"Page source snippet: {self.driver.page_source[2000:3000]}")
            raise Exception("No measures found in dropdown")

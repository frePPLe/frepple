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

from selenium.webdriver.common.by import By


class ForecastTableLocators(object):
    TABLE_DEFAULT = (By.CSS_SELECTOR, "table[id='fforecasttable']")

    TABLE_SAVE_BUTTON = (By.CSS_SELECTOR, 'button[id="save"]')
    TABLE_UNDO_BUTTON = (By.CSS_SELECTOR, 'button[id="undo"]')
    FORECAST_OVERRIDE_EDIT_APPLY_BUTTON = (By.CSS_SELECTOR, 'button[id="applyedit"]')

    FORECAST_OVERRIDE_CELLS = (By.CSS_SELECTOR, 'input[tabindex="7"]')
    FORECAST_OVERRIDE_STARTDATE = (
        By.CSS_SELECTOR,
        'input[id="editstartdate"]',
    )
    FORECAST_OVERRIDE_ENDDATE = (By.CSS_SELECTOR, 'input[id="editenddate"]')
    FORECAST_OVERRIDE_SET_INPUT = (By.CSS_SELECTOR, 'input[id="editset"]')

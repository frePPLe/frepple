/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

<script setup lang="js">
import {computed} from "vue";
import { useI18n } from 'vue-i18n';
import {useForecastsStore} from "@/stores/forecastsStore.js";

const { t: ttt, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useForecastsStore();

const detaildata = computed(() => store.forecastAttributes);

let isDirty = computed(() => (detaildata.value.oldForecastmethod !== detaildata.value.forecastmethod));

</script>

<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title mb-0 text-capitalize" data-translate=""><span>{{ ttt('parameters') }}</span></h5>
    </div>
    <div class="card-body">
      <table class="table table-borderless">
        <tbody><tr>
          <td style="white-space:nowrap"><span>{{ ttt('Forecast method') }}</span></td>
          <td>
            <div v-if="detaildata.forecastmethod" class="dropdown d-inline w-auto">
<!--          Vue dynamic class does not play well with bootstrap dropdown (could be a version specific issue?) so I used a dynamic style instead-->
              <button :style="isDirty ? 'background-color: #ff5252 !important; box-shadow: none !important;' : ''" class="dropdown-toggle form-control d-inline w-auto text-capitalize" name="forecastmethod" id="forecastmethodbutton" aria-expanded="false" type="button" data-bs-toggle="dropdown"
                      data-bs-auto-close="true" :title="ttt('Select forecast method, only possible at single item/location/customer level')">
                {{ ttt(detaildata.forecastmethod) }}&nbsp;&nbsp;
              </button>
              <ul :class="(detaildata.forecastmethod === 'aggregate') ? 'd-none' : ''" class="dropdown-menu" aria-labelledby="forecastmethodbutton">
                <li v-on:click="store.setForecastMethod('automatic')">
                  <a class="dropdown-item text-capitalize" id="automatic" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Automatic') }}</span></a>
                </li>
                <li v-on:click="store.setForecastMethod('constant')">
                  <a class="dropdown-item text-capitalize" id="constant" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Constant') }}</span></a>
                </li>
                <li v-on:click="store.setForecastMethod('trend')">
                  <a class="dropdown-item text-capitalize" id="trend" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Trend') }}</span></a>
                </li>
                <li v-on:click="store.setForecastMethod('seasonal')">
                  <a class="dropdown-item text-capitalize" id="seasonal" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Seasonal') }}</span></a>
                </li>
                <li v-on:click=" store.setForecastMethod('intermittent')">
                  <a class="dropdown-item text-capitalize" id="intermittent" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Intermittent') }}</span></a>
                </li>
                <li v-on:click="store.setForecastMethod('moving average')">
                  <a class="dropdown-item text-capitalize" id="movingaverage" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Moving average') }}</span></a>
                </li>
                <li v-on:click="store.setForecastMethod('manual')">
                  <a class="dropdown-item text-capitalize" id="manual" href="#" data-bs-dismiss="dropdown"><span>{{ ttt('Manual') }}</span></a>
                </li>
              </ul>
            </div>
          </td>
        </tr>

        <tr v-if="detaildata.forecastmethod !== 'aggregate'">
          <td translate="" style="white-space:nowrap"><span>{{ ttt('Selected forecast method') }}</span></td>
          <td class="ng-binding">
            {{ ttt(detaildata.forecast_out_method) }}
          </td>
        </tr>

        <tr v-if="detaildata.forecastmethod !== 'aggregate'">
          <td translate="" style="white-space:nowrap"><span>{{ ttt('Estimated forecast error') }}</span></td>
          <td class="ng-binding">
            {{ ttt(detaildata.forecast_out_smape) }}&nbsp;%
          </td>
        </tr>
        </tbody></table>
    </div>
  </div>
</template>


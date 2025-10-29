/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
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
                {{ detaildata.forecastmethod === 'movingaverage' ? ttt('Moving average') : ttt(detaildata.forecastmethod) }}&nbsp;&nbsp;
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
                <li v-on:click="store.setForecastMethod('movingaverage')">
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


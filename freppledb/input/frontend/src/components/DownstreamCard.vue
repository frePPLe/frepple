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

<script setup>
import { useI18n } from 'vue-i18n';
import {useOperationplansStore} from "@/stores/operationplansStore.js";
import {numberFormat} from "@common/utils.js";
import {computed} from "vue";

const { t: ttt } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useOperationplansStore();

const currentOperationplan = store.operationplan;

const props = defineProps({
  widget: {
    type: Array,
    default: () => []
  }
});

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const filteredDownstream = computed(() => {
  if (!store.operationplan["downstreamoperationplans"]) return [];
  return store.operationplan.downstreamoperationplans.filter(peg => peg[11] != 2);
});

</script>

<template>
  <div>
  <div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_downstream" aria-expanded="false" aria-controls="widget_downstream">
    <h5 class="card-title text-capitalize fs-5 me-auto">{{ ttt('downstream operations') }}</h5>
    <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
  </div>
  <div id="widget_downstream" class="card-body collapse" :class="{ 'show': !isCollapsed }">
    <table class="table table-sm table-hover table-borderless"><thead><tr>
      <td><b class="text-capitalize">{{ ttt('level') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('reference') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('type') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('operation') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('status') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('item') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('location') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('start date') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('end date') }}</b></td>
      <td><b class="text-capitalize">{{ ttt('quantity') }}</b></td>
    </tr></thead>
      <tbody>
      <tr v-if="!currentOperationplan.downstreamoperationplans"><td colspan="8">{{ ttt('no downstream information') }}</td></tr>
      <tr v-else v-for="(peg, key) in filteredDownstream" :key="key">
        <td>
          <span v-if="peg[11] == 0" class="fa fa-fw fa-caret-right" @click="store.expandOrCollapse(key, 'downstream')"></span>
          <span v-if="peg[11] == 1" class="fa fa-fw fa-caret-down" @click="store.expandOrCollapse(key, 'downstream')"></span>
          <span v-if="peg[11] == 3" class="fa fa-fw fa-circle-thin"></span>
          &nbsp;{{peg[0]}}
        </td>

        <td v-if="peg[2] === 'MO'">{{peg[1]}}
          <a :href="'/data/input/manufacturingorder/?noautofilter&parentreference=' + peg[1]" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="peg[2] === 'WO'">{{peg[1]}}
          <a :href="'/data/input/workorder/?noautofilter&parentreference=' + peg[1]" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="peg[2] === 'DO'">{{peg[1]}}
          <a :href="'/data/input/distributionorder/?noautofilter&parentreference=' + peg[1]" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="peg[2] === 'PO'">{{peg[1]}}
          <a :href="'/data/input/purchaseorder/?noautofilter&parentreference=' + peg[1]" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="peg[2] === 'DLVR'">{{peg[1]}}
          <a :href="'/data/input/deliveryorder/?noautofilter&parentreference=' + peg[1]" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="peg[2] === 'STCK'">{{peg[1]}}</td>

        <td>{{peg[2]}}</td>

        <td v-if="['MO', 'WO'].includes(peg[2])">{{peg[3]}}
          <a href="/detail/input/operation/key/" role="input/operation" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td v-if="!['MO', 'WO'].includes(peg[2])">{{peg[3]}}</td>
        <td>{{peg[4]}}</td>
        <td>{{peg[5]}}
          <a v-if="peg[5]" href="/detail/input/item/key/" role="input/item" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>
        <td>{{peg[6]}}
          <a v-if="peg[6]" href="/detail/input/location/key/" role="input/location" @click="opendetail(event)">
            <span class="fa fa-caret-right"></span>
          </a>
        </td>

        <td>{{ peg[7] }}</td>
        <td>{{ peg[8] }}</td>
        <td>{{ numberFormat(peg[9]) }} / {{ numberFormat(peg[10]) }}</td>
      </tr>
      </tbody>
    </table>
  </div>
  </div>
</template>

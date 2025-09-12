<script setup lang="js">
import {useForecastsStore} from "@/stores/forecastsStore";
import {computed} from "vue";
const store = useForecastsStore();

const props = defineProps({
  panelid: {
    type: String,
    default: null
  }
});

const data = computed(() => (props.panelid === 'I') ? store.itemTree: (props.panelid === 'L') ? store.locationTree: store.customerTree);
const modelName = (props.panelid === 'I') ? 'item': (props.panelid === 'L') ? 'location': 'customer';
console.log(14, data.value);
let currentHeight = (store.preferences.height || 240);

function toggleRowVisibility(rowIndex) {
  console.log(19, data.value[rowIndex]);
  data.value[rowIndex].expanded = data.value[rowIndex].expanded === 1 ? 0 : 1;
  const isExpanded = data.value[rowIndex].expanded === 1;
  for (let i = rowIndex+1; i < data.value.length; i++) {
    console.log(23, 'index', i, isExpanded, data.value[i].item);
    console.log(24, data.value[i].lvl, data.value[i].lvl+1)
    if (data.value[i].lvl < data.value[rowIndex].lvl+1) break;
    if (data.value[i].lvl > data.value[rowIndex].lvl+1) continue;
    data.value[i].visible = isExpanded ;
  }
}

</script>

<template>
  <div class="card " style="min-height: 100px; height: 100%;" id="{{modelName + 'panel'}}">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0" translate=""><span>{{ modelName }}</span></h5>
    </div>
    <div class="card-body ps-0 pe-0 pt-2 pb-2"
         :style="{'height':  currentHeight - 31 + 'px'}"
         style="overflow: auto">
      <div class="">
        <div id="{{modelName + 'table'}}">
          <div class="d-table w-100">
            <div style="float: left; overflow:hidden;">&nbsp;</div>
            <div class="ms-auto text-right">
              <span v-for="bucketname in store.treeBuckets" :key="bucketname" class="numbervalues">
                <strong><small>{{ bucketname }}</small></strong>
              </span>
            </div>
          </div>

          <div v-for="(row, index) in data" :key="row[modelName]" class="d-flex flex-wrap evtitemrow" v-on:click="toggleRowVisibility(index)">
            <div style="overflow:visible;" :style="'padding-left: ' + row.lvl * 13 + 'px'">
              &nbsp;<span v-if="row.children && row.visible" class="fa" :class="row.expanded == 1 ? 'fa-caret-down' : 'fa-caret-right'"></span>
              <span v-if="row.visible" style="white-space:nowrap">{{row[modelName]}}</span>
            </div>
            <div v-if="row.visible" class="ms-auto text-right">
              <span v-for="val in row.values" :key="val.bucketname" class="numbervalues">{{val.value}}</span>
            </div>
          </div>
<!--          <div level="1">-->
<!--            <div index="1" class="d-flex flex-wrap evtitemrow" style="">-->
<!--              <div style="overflow:visible; padding-left: 13px">&nbsp;<span>&nbsp;</span><span-->
<!--                style="white-space:nowrap">chair</span></div>-->
<!--              <div class="ms-auto text-right"><span class="numbervalueslast">294</span><span-->
<!--                class="numbervalues">292</span><span class="numbervalues">286</span></div>-->
<!--            </div>-->
<!--            <div index="2" class="d-flex flex-wrap evtitemrow" style="">-->
<!--              <div style="overflow:visible; padding-left: 13px">&nbsp;<span>&nbsp;</span><span-->
<!--                style="white-space:nowrap">varnished chair</span></div>-->
<!--              <div class="ms-auto text-right"><span class="numbervalueslast">147</span><span-->
<!--                class="numbervalues">145</span><span class="numbervalues">143</span></div>-->
<!--            </div>-->
<!--            <div index="3" class="d-flex flex-wrap evtitemrow" style="">-->
<!--              <div style="overflow:visible; padding-left: 13px">&nbsp;<span>&nbsp;</span><span-->
<!--                style="white-space:nowrap">square table</span></div>-->
<!--              <div class="ms-auto text-right"><span class="numbervalueslast">28</span><span-->
<!--                class="numbervalues">28</span><span class="numbervalues">28</span></div>-->
<!--            </div>-->
<!--            <div index="4" class="d-flex flex-wrap evtitemrow bg-light" style="">-->
<!--              <div style="overflow:visible; padding-left: 13px">&nbsp;<span>&nbsp;</span><span-->
<!--                style="white-space:nowrap">round table</span></div>-->
<!--              <div class="ms-auto text-right"><span class="numbervalueslast">23</span><span-->
<!--                class="numbervalues">24</span><span class="numbervalues">22</span></div>-->
<!--            </div>-->
<!--          </div>-->
        </div>
      </div>
    </div>
  </div>
</template>

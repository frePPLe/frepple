<script setup lang="js">
import {useForecastsStore} from "@/stores/forecastsStore";
import {computed, toRaw} from "vue";
const store = useForecastsStore();

const props = defineProps({
  panelid: {
    type: String,
    default: null
  }
});

const data = computed(() => (props.panelid === 'I') ? store.itemTree: (props.panelid === 'L') ? store.locationTree: store.customerTree);
const modelName = (props.panelid === 'I') ? 'item': (props.panelid === 'L') ? 'location': 'customer';
console.log(14, toRaw(data).value);
const currentHeight = computed(() => (store.dataRowHeight || 240));

function selectILCobject(model, rowIndex) {
  console.log(19, data.value[rowIndex][model], 'children: ', data.value[rowIndex]['children'],'model: ', model, 'expanded: ', data.value[rowIndex].expanded === 0);

  store.setItemLocationCustomer(model, data.value[rowIndex][model], data.value[rowIndex]['children'], data.value[rowIndex]['lvl'],data.value[rowIndex].expanded === 0);
  if (data.value[rowIndex]['children']) {
    toggleRowVisibility(rowIndex);
  }

}

function toggleRowVisibility(rowIndex) {
  // Should this be moved to the store? We are manipulating store values directly.
  console.log(29, 'toggleRowVisibility', rowIndex, 'data: ', data.value[rowIndex], 'expanded: ', data.value[rowIndex].expanded === 1, 'children: ', data.value[rowIndex]['children'])
  data.value[rowIndex].expanded = data.value[rowIndex].expanded === 1 ? 0 : 1;
  const isExpanded = data.value[rowIndex].expanded === 1;
  let lineCount = 0;
  for (let i = rowIndex+1; i < data.value.length; i++) {
    if (data.value[i].lvl < data.value[rowIndex].lvl+1) break;
    if ((data.value[i].lvl > data.value[rowIndex].lvl+1) && isExpanded) continue;
    if (isExpanded) {
      data.value[i].visible = isExpanded;
    } else {
      lineCount++;
    }
  }
  if (lineCount > 0) {
    // data is in sync with the store... this splice will change the tree data in the store
    data.value.splice(rowIndex+1, lineCount);
  }
}

</script>

<template>
  <div class="card " :style="{'height':  currentHeight - 31 + 'px'}" style="min-height: 100px; max-height: 50vh" :id="modelName + 'panel'">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0" translate=""><span>{{ modelName }}</span></h5>
    </div>
    <div class="card-body ps-0 pe-0 pt-2 pb-2"  style="overflow: auto">
      <div class="">
        <div :id="modelName + 'table'">
          <div class="d-flex w-100">
            <div class="w-100 d-flex justify-content-end text-start">
              <span v-for="bucketname in store.treeBuckets" :key="bucketname" class="numbervalues">
                <strong><small>{{ bucketname }}</small></strong>
              </span>
            </div>
          </div>

          <div v-for="(row, index) in data" :key="row[modelName]" :class="(row[modelName] === store[modelName].name) ? 'bg-light' : ''" class="d-flex flex-wrap evtitemrow" v-on:click="selectILCobject(modelName, index)">
            <div style="overflow:visible;" :style="'padding-left: ' + row.lvl * 13 + 'px'">
              &nbsp;<span v-if="row.children && row.visible" class="fa" :class="row.expanded === 1 ? 'fa-caret-down' : 'fa-caret-right'"></span>
              <span v-if="row.visible" style="white-space:nowrap">{{row[modelName]}}</span>
            </div>
            <div v-if="row.visible" class="ms-auto d-flex justify-content-end text-start">
              <span v-for="val in row.values" :key="val.bucketname" class="numbervalues">{{val.value}}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

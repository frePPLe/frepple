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
import { useForecastsStore } from '@/stores/forecastsStore';
import AttributesTab from './AttributesTab.vue';
import ForecastTab from './ForecastTab.vue';
import CommentsTab from './CommentsTab.vue';
import {computed} from "vue";

const store = useForecastsStore();
const database = computed(() => window.database);

function save(saveAll) {
  console.log(14, 'save', saveAll);

  // If on the comments tab and there are changes, save the comment
  if (store.hasChanges) {
    store.saveForecastChanges();
  }
}

function undo() {
  console.log(14, 'undo');

  if (store.hasChanges) {
    store.undo();
  }
}
</script>

<template>
  <div>
    <div class="row">
      <div class="col-auto d-flex">
      <span class="d-flex">
        <div class="form-inline">
          <button
            id="save"
            class="btn btn-primary me-1"
            @click="save(false)"
            data-bs-toggle="tooltip"
            :disabled="!store.hasChanges"
            :class="store.hasChanges ? 'btn-danger' : ''"
            data-bs-original-title="Save changes to the database">
            Save
          </button>
          <button
            id="undo"
            class="btn btn-primary"
            @click="undo()"
            data-bs-toggle="tooltip"
            :disabled="!store.hasChanges"
            :class="store.hasChanges ? 'btn-danger' : ''"
            data-bs-original-title="Undo changes">
            Undo
          </button>
        </div>
      </span>

      <span v-for="(model, index) in store.currentSequence" :key="model">
        <span v-if="index > 0">&nbsp;-&nbsp;</span>
        <span v-if="model==='I'">{{ store.item.Name }}{{ store.item.Description ? " (" + store.item.Description + ")" : "" }}
          <a :href="'/' + database + '/detail/input/item/' + store.item.Name + '/'" onclick.stop=""><span class="fa fa-caret-right"></span></a>
        </span>
        <span v-if="model==='L'">{{ store.location.Name }}{{ store.location.Description ? " (" + store.location.Description + ")" : ""}}
          <a :href="'/' + database + '/detail/input/location/' + store.location.Name + '/'" onclick.stop=""><span class="fa fa-caret-right"></span></a>
        </span>
        <span v-if="model==='C'">{{ store.customer.Name }}{{ store.customer.Description ?  " (" + store.customer.Description + ")" : "" }}
          <a :href="'/' + database + '/detail/input/customer/' + store.customer.Name + '/'" onclick.stop=""><span class="fa fa-caret-right"></span></a>
        </span>
      </span>

      </div>
      <div id="tabs" class="col-auto form-inline ms-auto">
        <ul class="nav nav-tabs">
          <li class="nav-item" id="attributestab" role="presentation" @click="store.setShowTab('attributes')">
            <a :class="['text-capitalize', {'nav-link': true, 'active': store.showTab === 'attributes'}]" class="text-capitalize nav-link">
              <span>attributes</span>
            </a>
          </li>
          <li class="nav-item" id="forecasttab" role="presentation" @click="store.setShowTab('forecast')">
            <a :class="['text-capitalize', {'nav-link': true, 'active': store.showTab === 'forecast'}]" class="text-capitalize nav-link">
              <span>forecast</span>
            </a>
          </li>
          <li class="nav-item" id="commentstab" role="presentation" @click="store.setShowTab('comments')">
            <a :class="['text-capitalize', {'nav-link': true, 'active': store.showTab === 'comments'}]" class="text-capitalize nav-link">
              <span>comments</span>
            </a>
          </li>
        </ul>
      </div>
    </div>

    <div class="tab-content mt-3">
      <AttributesTab v-if="store.showTab === 'attributes'" />
      <ForecastTab v-if="store.showTab === 'forecast'" />
      <CommentsTab v-if="store.showTab === 'comments'" />
    </div>
  </div>
</template>

/* * Copyright (C) 2025 by frePPLe bv * * Permission is hereby granted, free of charge, to any
person obtaining * a copy of this software and associated documentation files (the * "Software"), to
deal in the Software without restriction, including * without limitation the rights to use, copy,
modify, merge, publish, * distribute, sublicense, and/or sell copies of the Software, and to *
permit persons to whom the Software is furnished to do so, subject to * the following conditions: *
* The above copyright notice and this permission notice shall be * included in all copies or
substantial portions of the Software. * * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF * MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION * OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION * WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE * */

<script setup lang="js">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import { VueCal } from 'vue-cal';
import 'vue-cal/style.css';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const language = document.documentElement.lang;

const store = useOperationplansStore();

// Calendar view state
const currentView = ref('month');
const selectedDate = ref(new Date());

// Grouping and calendar modes from window (set by Django template)
const groupingcfg = computed(() => window.groupingcfg || {});
const calendarmodes = computed(() => ({
  start: ttt('View start events'),
  end: ttt('View end events'),
  start_end: ttt('View start and end events'),
  duration: ttt('View full duration'),
}));

// to be populated with events from the backend
const events = ref([]);

const eventCount = computed(() => events.value.length);

const title = computed(() => {
  const date = new Date(selectedDate.value);
  const options = { year: 'numeric', month: 'long' };
  if (currentView.value === 'day') {
    return date.toLocaleDateString(undefined, { ...options, day: 'numeric' });
  } else if (currentView.value === 'week') {
    const startOfWeek = new Date(date);
    startOfWeek.setDate(date.getDate() - date.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    return `${startOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`;
  }
  return date.toLocaleDateString(undefined, options);
});

function setView(view) {
  currentView.value = view;
}

function movePrev() {
  const date = new Date(selectedDate.value);
  if (currentView.value === 'day') {
    date.setDate(date.getDate() - 1);
  } else if (currentView.value === 'week') {
    date.setDate(date.getDate() - 7);
  } else {
    date.setMonth(date.getMonth() - 1);
  }
  selectedDate.value = date;
}

function moveNext() {
  const date = new Date(selectedDate.value);
  if (currentView.value === 'day') {
    date.setDate(date.getDate() + 1);
  } else if (currentView.value === 'week') {
    date.setDate(date.getDate() + 7);
  } else {
    date.setMonth(date.getMonth() + 1);
  }
  selectedDate.value = date;
}

onMounted(async () => {
  await nextTick();
  window.setHeights();
});
</script>

<template>
  <Teleport to="#calendar" v-if="store.isCalendarMode">
    <div class="calendar-board">
      <!-- Calendar Header -->
      <div class="row calendar-navbar">
        <div class="col-auto me-auto ver-align-middle">
          <span v-if="Object.keys(groupingcfg).length > 0">
            <button
              class="dropdown-toggle form-control"
              style="width: auto"
              type="button"
              name="grouping"
              data-bs-toggle="dropdown"
            >
              {{
                store.grouping ? ttt('Group by ') + groupingcfg[store.grouping] : ttt('No grouping')
              }}&nbsp;&nbsp;<i class="caret"></i>
            </button>
            <ul class="dropdown-menu" aria-labelledby="grouping">
              <li><a class="dropdown-item" @click="store.setGrouping(null)">No grouping</a></li>
              <li v-for="(label, name) in groupingcfg" :key="name">
                <a class="dropdown-item" @click="store.setGrouping(name)">Group by {{ label }}</a>
              </li>
            </ul>
          </span>
        </div>
        <div class="col-1 hor-align-right ver-align-middle">
          <button type="button" class="btn btn-primary btn-sm" @click="movePrev">
            <i class="fa fa-chevron-left"></i>
          </button>
        </div>
        <div class="calendar-header col-2">
          {{ ttt(title) }}
          <span class="badge bg-primary">{{ eventCount }}</span>
        </div>
        <div class="col-1 alignleft ver-align-middle">
          <button type="button" class="btn btn-primary btn-sm" @click="moveNext">
            <i class="fa fa-chevron-right"></i>
          </button>
        </div>
        <div class="col-auto ms-auto ver-align-middle">
          <div class="dropdown">
            <button
              class="form-control dropdown-toggle w-auto"
              type="button"
              aria-expanded="false"
              name="calmode"
              data-bs-toggle="dropdown"
            >
              {{ calendarmodes[store.calendarmode] }}&nbsp;&nbsp;<i class="caret"></i>
            </button>
            <ul class="dropdown-menu" aria-labelledby="calmode">
              <li>
                <a class="dropdown-item" @click="store.setCalendarMode('start')">{{
                  calendarmodes['start']
                }}</a>
              </li>
              <li>
                <a class="dropdown-item" @click="store.setCalendarMode('end')">{{
                  calendarmodes['end']
                }}</a>
              </li>
              <li>
                <a class="dropdown-item" @click="store.setCalendarMode('start_end')">{{
                  calendarmodes['start_end']
                }}</a>
              </li>
              <li>
                <a class="dropdown-item" @click="store.setCalendarMode('duration')">{{
                  calendarmodes['duration']
                }}</a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- vue-cal Component -->
      <VueCal
        :locale="language"
        theme="vuecal-frepple"
        :selected-date="selectedDate"
        :active-view="currentView"
        :events="events"
        :views="['month', 'week', 'day']"
        :disable-views="[]"
        class="calendar-vuecal vuecal-frepple"
        @view-change="(view) => (currentView = view.view)"
      >
        <template #title="{ title: viewTitle }">
          {{ viewTitle }}
        </template>
      </VueCal>
    </div>
  </Teleport>
</template>

<style scoped>
.calendar-board {
  padding: 10px;
}

.calendar-navbar {
  margin-bottom: 15px;
  align-items: center;
}

.calendar-header {
  text-align: center;
  font-weight: bold;
  font-size: 1.1em;
}

.ver-align-middle {
  vertical-align: middle;
}

.hor-align-right {
  text-align: right;
}

.alignleft {
  text-align: left;
}
</style>

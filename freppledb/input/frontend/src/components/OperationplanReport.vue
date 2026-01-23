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
import { computed, ref, watch, onMounted, nextTick } from 'vue';
import { useOperationplansStore } from '../stores/operationplansStore.js';
import { useI18n } from 'vue-i18n';

const store = useOperationplansStore();
const { t } = useI18n({ useScope: 'global', inheritLocale: true });

const mode = computed(() => store.mode);
const calendarmode = computed(() => store.calendarmode);
const showTop = computed(() => store.showTop);
const showChildren = computed(() => store.showChildren);

const showGantt = ref(false);
const grouping = ref(null);
const groupingdir = ref('asc');
const dataRowHeight = ref(null);

const isModeTable = computed(() => mode.value === 'table');
const isCalendarMode = computed(() => mode.value.startsWith('calendar'));
const isKanbanMode = computed(() => mode.value === 'kanban');
const isGanttMode = computed(() => mode.value === 'gantt');

onMounted(() => {
  if (window.preferences) {
    store.setMode(window.preferences.mode || 'table');
    store.setCalendarMode(window.preferences.calendarmode || 'month');
    grouping.value = window.preferences.grouping || null;
    groupingdir.value = window.preferences.groupingdir || 'asc';

    if (window.preferences.showTop !== undefined) {
      store.setShowTop(window.preferences.showTop);
    }
    if (window.preferences.showChildren !== undefined) {
      store.setShowChildren(window.preferences.showChildren);
    }

    if (window.preferences.height) {
      dataRowHeight.value = window.preferences.height;
    }
  }

  showGantt.value = window.showGantt || false;
  store.setPreferences(window.preferences || {});
});

// Methods
const setMode = (newMode) => {
  store.setMode(newMode);
  if (newMode.startsWith('calendar')) {
    const calMode = newMode.replace('calendar', '');
    store.setCalendarMode(calMode);
  }
  store.savePreferences();
};

const toggleShowTop = () => {
  store.setShowTop(!showTop.value);
  store.savePreferences();
};

const toggleShowChildren = () => {
  store.setShowChildren(!showChildren.value);
  store.savePreferences();
};

const handleResize = (e) => {
  const mainElement = document.getElementById('content-main');
  if (mainElement) {
    const newHeight = Math.floor(mainElement.offsetHeight);
    if (newHeight > 0) {
      dataRowHeight.value = newHeight;
      store.setDataRowHeight(newHeight);
    }
  }
};

const handleCalendarRangeChanged = (startDate, endDate) => {
  store.setViewDates(startDate, endDate);
};

const handleEventSelected = (event) => {
  store.displayInfo(event);
};

// Watch for mode changes and trigger appropriate data loading
watch(mode, async (newMode) => {
  await nextTick();
  if (newMode === 'kanban') {
    // Trigger kanban data loading
    console.log('Loading kanban data:', store.currentFilter);
  } else if (newMode === 'gantt') {
    // Trigger gantt data loading
    console.log('Loading gantt data:', store.currentFilter);
  } else if (newMode.startsWith('calendar')) {
    // Trigger calendar data loading
    console.log('Loading calendar data:', store.currentFilter);
  }
});

</script>

<template>
  <div class="operationplan-report">
    <!-- Toolbar  -->
    <div class="toolbar mb-3">
      <div class="btn-group" role="group">
        <button
          id="showTop"
          type="button"
          class="btn btn-sm btn-outline-primary"
          :class="{ active: showTop }"
          @click="toggleShowTop"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="t('display top level')"
        >
          <svg width="100%" height="1.2em" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect height="42" width="100" rx="10" ry="10" class="fill-primary" />
            <rect height="38" x="7" y="55" width="33" rx="10" ry="10" class="stroke-primary" stroke-width="14" />
            <rect height="38" x="60" y="55" width="33" rx="10" ry="10" class="stroke-primary" stroke-width="14" />
          </svg>
        </button>
        <button
          id="showChildren"
          type="button"
          class="btn btn-sm btn-outline-primary"
          :class="{ active: showChildren }"
          @click="toggleShowChildren"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="t('display child level')"
        >
          <svg width="100%" height="1.2em" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect height="35" x="7" y="7" width="86" rx="10" ry="10" class="stroke-primary" stroke-width="14" />
            <rect height="45" x="0" y="55" width="45" rx="10" ry="10" class="fill-primary" />
            <rect height="45" x="55" y="55" width="45" rx="10" ry="10" class="fill-primary" />
          </svg>
        </button>
      </div>

      <!-- Mode selection buttons -->
      <div class="btn-group ms-2" role="group">
        <!-- Table Mode -->
        <button
          id="gridmode"
          type="button"
          class="btn btn-sm btn-primary"
          :class="{ active: isModeTable }"
          @click="setMode('table')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="t('display table')"
        >
          <span class="fa fa-table fa-lg"></span>
        </button>

        <!-- Kanban Mode -->
        <button
          id="kanbanmode"
          type="button"
          class="btn btn-sm btn-primary"
          :class="{ active: isKanbanMode }"
          @click="setMode('kanban')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="t('display kanban cards')"
        >
          <span class="fa fa-columns fa-lg"></span>
        </button>

        <!-- Calendar Mode Dropdown -->
        <div class="btn-group dropdown" role="group">
          <button
            id="calendarmode"
            type="button"
            class="btn btn-sm btn-primary dropdown-toggle"
            :class="{ active: isCalendarMode }"
            data-bs-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :title="t('display calendar')"
          >
            <span class="fa fa-calendar-o"></span>
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li class="dropdown-item">
              <a href="#" @click.prevent="setMode('calendarmonth')">{{ t('month') }}</a>
            </li>
            <li class="dropdown-item">
              <a href="#" @click.prevent="setMode('calendarweek')">{{ t('week') }}</a>
            </li>
            <li class="dropdown-item">
              <a href="#" @click.prevent="setMode('calendarday')">{{ t('day') }}</a>
            </li>
          </ul>
        </div>

        <!-- Gantt Mode -->
        <button
          v-if="showGantt"
          id="ganttmode"
          type="button"
          class="btn btn-sm btn-primary"
          :class="{ active: isGanttMode }"
          @click="setMode('gantt')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :title="t('display Gantt chart')"
        >
          <span class="fa fa-align-left fa-lg"></span>
        </button>
      </div>

      <!-- Additional toolbar buttons (add, copy, delete, etc.) -->
      <div class="btn-group ms-2" role="group">
        <slot name="toolbar-buttons"></slot>
      </div>
    </div>

    <!-- Main content area with different views -->
    <div id="content-main" class="operationplan-content row text-center" style="min-height: 150px; margin-top: 0.7em" @resize="handleResize">
      <div class="col-md-12">
        <!-- Table View -->
        <div v-if="isModeTable" class="table-view">
          <slot name="table-view">
            <table id="grid" class="table table-striped" style="background-color: white"></table>
            <div id="gridpager"></div>
          </slot>
        </div>


<!--        <div v-if="isCalendarMode" id="calendar" class="calendar-view col-md-12">-->
<!--          <slot-->
<!--            name="calendar-view"-->
<!--            :mode="calendarmode"-->
<!--            @range-changed="handleCalendarRangeChanged"-->
<!--            @event-selected="handleEventSelected"-->
<!--          >-->
<!--            <calendar-->
<!--              :mode="calendarmode"-->
<!--              @range-changed="handleCalendarRangeChanged"-->
<!--              @event-selected="handleEventSelected"-->
<!--            ></calendar>-->
<!--          </slot>-->
<!--        </div>-->

<!--        <div v-if="isKanbanMode" id="kanban" class="kanban-view row">-->
<!--          <slot name="kanban-view"></slot>-->
<!--        </div>-->

<!--        <div v-if="isGanttMode" id="gantt" class="gantt-view row">-->
<!--          <slot name="gantt-view"></slot>-->
<!--        </div>-->
      </div>
    </div>

    <span id="resize-handle" class="fa fa-bars handle" style="display: inline-block"></span>

    <div class="details-panel">
      <slot name="details-panel"></slot>
    </div>
  </div>
</template>

<style scoped>
.operationplan-report {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: auto;
}

.toolbar {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.operationplan-content {
  flex: 1;
  overflow: auto;
  background-color: white;
  min-height: 150px;
  margin-top: 0.7em;
}

.table-view,
.calendar-view,
.kanban-view,
.gantt-view {
  width: 100%;
  height: 100%;
}

.details-panel {
  flex: 0 0 auto;
  border-top: 1px solid #dee2e6;
  overflow: auto;
}

.handle {
  cursor: ns-resize;
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
  border-bottom: 1px solid #dee2e6;
}
</style>

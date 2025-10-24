<script setup>
import {computed, nextTick, onBeforeUnmount, ref, watch} from 'vue';
import {useForecastsStore} from '@/stores/forecastsStore';
import {useI18n} from 'vue-i18n';

const { t, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});
const store = useForecastsStore();

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
});


const emit = defineEmits(['close']);

// const showDescriptions = ref(store.preferences.showdescription || false);
const showDescriptions = computed(() => store.showDescription || false);

const availableMeasures = computed(() => {
  const hidden = Object.values(store.measures).filter(measure =>
      !store.tableRows.includes(measure.name)
  );
  return hidden.sort((a, b) => a.label.localeCompare(b.label));
});

const selectedMeasures = computed(() => {
  return store.tableRows.map(rowName => ({
    name: rowName,
    label: store.measures[rowName]?.label || rowName
  }));
});

const showModal = () => {
  const popupElement = document.getElementById('popup');
  if (popupElement) {
    popupElement.innerHTML = getModalContent();

    // Use the global showModal function
    window.showModal('popup');

    // Initialize Sortable after modal is shown
    nextTick(() => {
      initializeSortable();
      setupEventHandlers();
    });
  }
};

const hideModal = () => {
  window.hideModal('popup');
  emit('close');
};

let selectedSortable = null;
let availableSortable = null;

const getModalContent = () => {
  return `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${t("Customize")}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" id="customize-close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-6">
              <div class="card">
                <div class="card-header">${t('Available Cross')}</div>
                <div class="card-body">
                  <ul id="available-measures" class="list-group" style="height: 160px; overflow-y: scroll; border: 0px;">
                    ${availableMeasures.value.map(measure =>
      `<li class="list-group-item" style="cursor: move; border: 0px;" data-value="${measure.name}">${measure.label}</li>`
  ).join('')}
                  </ul>
                </div>
              </div>
            </div>
            <div class="col-6">
              <div class="card">
                <div class="card-header">${t('Selected Cross')}</div>
                <div class="card-body">
                  <ul id="selected-measures" class="list-group" style="height: 160px; overflow-y: scroll;; border: 0px;">
                    ${selectedMeasures.value.map(measure =>
      `<li class="list-group-item" style="cursor: move;; border: 0px;" data-value="${measure.name}">${measure.label}</li>`
  ).join('')}
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div class="row mt-3">
            <div class="col-12">
              <input class="form-check-input" type="checkbox" id="showdescription" ${store.showDescription ? 'checked' : ''}>
              <label for="showdescription">&nbsp;&nbsp;${t('Show descriptions')}</label>
            </div>
          </div>
        </div>
        <div class="modal-footer justify-content-between">
          <input type="submit" id="cancelCustbutton" role="button" class="btn btn-gray" value="${t('Cancel')}">
          <input type="submit" id="resetCustbutton" role="button" class="btn btn-primary" value="${t('Reset')}">
          <input type="submit" id="okCustbutton" role="button" class="btn btn-primary" value="${t('OK')}">
        </div>
      </div>
    </div>
  `;
};

const initializeSortable = () => {
  const selectedList = document.getElementById('selected-measures');
  const availableList = document.getElementById('available-measures');

  if (selectedList && availableList && window.Sortable) {
    // Clean up existing instances
    if (selectedSortable) selectedSortable.destroy();
    if (availableSortable) availableSortable.destroy();

    // Initialize Sortable for selected measures
    selectedSortable = window.Sortable.create(selectedList, {
      group: {
        name: 'measures',
        put: ['available-measures']
      },
      animation: 100,
      onAdd: () => updateTableRows(),
      onSort: () => updateTableRows()
    });

    // Initialize Sortable for available measures
    availableSortable = window.Sortable.create(availableList, {
      group: {
        name: 'available-measures',
        put: ['measures']
      },
      animation: 100,
      onAdd: () => updateTableRows()
    });
  }
};

const setupEventHandlers = () => {
  // Close button handler
  const closeBtn = document.getElementById('customize-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', hideModal);
  }

  // Cancel button handler
  const cancelBtn = document.getElementById('cancelCustbutton');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', hideModal);
  }

  // Reset button handler
  const resetBtn = document.getElementById('resetCustbutton');
  if (resetBtn) {
    resetBtn.addEventListener('click', handleReset);
  }

  // OK button handler
  const okBtn = document.getElementById('okCustbutton');
  if (okBtn) {
    okBtn.addEventListener('click', handleOk);
  }

  // Show descriptions checkbox handler
  const showDescCheckbox = document.getElementById('showdescription');
  if (showDescCheckbox) {
    showDescCheckbox.addEventListener('change', handleShowDescriptionsChange);
  }
};

const updateTableRows = () => {
  const selectedList = document.getElementById('selected-measures');
  if (selectedList) {
    const newTableRows = [];
    selectedList.querySelectorAll('li').forEach(li => {
      const measureName = li.getAttribute('data-value');
      if (measureName) {
        newTableRows.push(measureName);
      }
    });
    store.tableRows = newTableRows;
  }
};

const handleShowDescriptionsChange = (event) => {
  store.showDescription = event.target.checked;
  store.preferences.showdescription = event.target.checked;
};

const handleReset = () => {
  // Reset to default measures like in AngularJS version
  const defaultMeasures = [];
  Object.keys(store.measures).forEach(key => {
    const measure = store.measures[key];
    if (measure.initially_hidden !== true &&
        (measure.mode_future !== 'hidden' || measure.mode_past !== 'hidden')) {
      defaultMeasures.push(key);
    }
  });
  store.tableRows = defaultMeasures;
  store.showDescription = event.target.checked;
  savePreferences(() => {
    window.location.href = window.location.href;
  });
};

const handleOk = () => {
  updateTableRows();
  savePreferences(() => {
    window.location.href = window.location.href;
  });
};

const savePreferences = (callback) => {
  store.savePreferences().then(() => {
    hideModal();
    if (callback) callback();
  }).catch(error => {
    console.error('Error saving preferences:', error);
    hideModal();
    if (callback) callback();
  });
};

// Watch for show prop changes
watch(() => props.show, (newValue) => {
  if (newValue) {
    showModal();
  }
});

// Cleanup on unmount
onBeforeUnmount(() => {
  if (selectedSortable) {
    selectedSortable.destroy();
  }
  if (availableSortable) {
    availableSortable.destroy();
  }
});

// Expose showModal method for external use
defineExpose({
  showModal
});
</script>

<template>
  <!-- This component now uses the existing #popup modal, so no template content needed -->
</template>

<style scoped>
/* No styles needed since we're using the existing modal system */
</style>
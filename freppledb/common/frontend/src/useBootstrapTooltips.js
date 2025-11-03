/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

import { onMounted, onUnmounted, ref } from 'vue';

export function useBootstrapTooltips(options = {}) {
  const { autoDispose = true } = options;
  const tooltipInstances = ref([]);

  const initTooltips = () => {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');

    tooltipInstances.value = [...tooltipTriggerList].map(tooltipTriggerEl => {
      // Check if tooltip is already initialized to avoid duplicates
      const existingTooltip = window.bootstrap.Tooltip.getInstance(tooltipTriggerEl);
      if (existingTooltip) {
        return existingTooltip;
      }
      return new window.bootstrap.Tooltip(tooltipTriggerEl);
    });
  };

  const disposeTooltips = () => {
    tooltipInstances.value.forEach(tooltip => {
      if (tooltip) {
        tooltip.dispose();
      }
    });
    tooltipInstances.value = [];
  };

  onMounted(() => {
    initTooltips();
  });

  if (autoDispose) {
    onUnmounted(() => {
      disposeTooltips();
    });
  }

  return {
    initTooltips,
    disposeTooltips
  };
}
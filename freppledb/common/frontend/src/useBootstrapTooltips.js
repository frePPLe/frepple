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

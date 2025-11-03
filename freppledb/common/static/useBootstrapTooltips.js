import { ref as u, onMounted as a, onUnmounted as l } from "vue";
function d(r = {}) {
  const { autoDispose: p = !0 } = r, t = u([]), n = () => {
    const o = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    t.value = [...o].map((s) => {
      const i = window.bootstrap.Tooltip.getInstance(s);
      return i || new window.bootstrap.Tooltip(s);
    });
  }, e = () => {
    t.value.forEach((o) => {
      o && o.dispose();
    }), t.value = [];
  };
  return a(() => {
    n();
  }), p && l(() => {
    e();
  }), {
    initTooltips: n,
    disposeTooltips: e
  };
}
export {
  d as useBootstrapTooltips
};

import {onMounted, onUnmounted, ref} from 'vue';

const isEmpty = data => data === null || data === undefined;

const isObject = data => data && typeof data === 'object';

const isBlank = data => {
  return (
    isEmpty(data) ||
    (Array.isArray(data) && data.length === 0) ||
    (isObject(data) && Object.keys(data).length === 0) ||
    (typeof data === 'string' && data.trim().length === 0)
  );
};

const getURLprefix = () => {
  const database = ref(window.database); // assuming database is defined globally
  return database.value === 'default' ? '' : `/${database.value}`;
};

// Date formatting filter, expecting a moment instance as input
const dateTimeFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  // Using Intl.DateTimeFormat for modern date formatting
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
};

// const getDjangoTemplateVariable = variableName => {
//   const result = ref(window[variableName]); // assuming variable is defined globally
//   console.log(39, result)
//   return result;
// };

function getDjangoTemplateVariable(key, options = { reactive: false }) {
  const result = ref(window[key]);

  if (false && options.reactive) {
    onMounted(() => {
      // First I need to intercept property changes, this can be done with a Proxy (this is very advanced stuff)
      window[key] = new Proxy(window[key] || {}, {
        set(target, property, value) {
          target[property] = value;
          // Dispatch a custom event when properties change
          window.dispatchEvent(new CustomEvent(`${key}Changed`, {
            detail: { property, value, newState: target }
          }));
          return true;
        }
      });

      // Listen for our custom event, I use structured clone because this is a general function so it should also work for a deeper object
      const updateValue = (event) => {
        result.value = structuredClone(event.detail.newState);
      };

      window.addEventListener(`${key}Changed`, updateValue);

      // Initial value
      result.value = structuredClone(window[key]);

      // Cleanup
      onUnmounted(() => {
        window.removeEventListener(`${key}Changed`, updateValue);
      });
    });
  }

  return result;
}

const dateFormat = (input, fmt) => {
  if (!input) return '';
  const date = new Date(input);
  // Using Intl.DateTimeFormat for date-only formatting
  const formatter = new Intl.DateTimeFormat('default', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return fmt ? date.toLocaleString() : formatter.format(date);
};

export {
  isEmpty,
  isObject,
  isBlank,
  getURLprefix,
  dateTimeFormat,
  dateFormat,
  getDjangoTemplateVariable,
};

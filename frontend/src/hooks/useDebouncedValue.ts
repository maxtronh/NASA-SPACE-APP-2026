import { useEffect, useState } from "react";

/**
 * Custom hook to debounce values (e.g. slider inputs, search query text).
 * Prevents interactive request storms while keeping UI responsiveness immediate.
 */
export function useDebouncedValue<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebounced(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debounced;
}

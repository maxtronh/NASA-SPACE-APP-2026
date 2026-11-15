"use client";

import type { KeyboardEvent } from "react";

/**
 * WAI-ARIA tabs pattern keyboard support for a single-select horizontal
 * tablist. Arrow keys wrap between tabs and Home/End jump to the ends; focus
 * follows selection so the next Tab press leaves the tablist.
 *
 * Each tab must sit directly inside the element with `role="tablist"` and carry
 * a `data-tab-value` attribute matching its value.
 */
export function handleTabKeyDown<T extends string>(
  event: KeyboardEvent<HTMLButtonElement>,
  order: readonly T[],
  current: T,
  onChange: (value: T) => void
) {
  const index = order.indexOf(current);
  if (index === -1) return;

  let nextIndex: number;
  switch (event.key) {
    case "ArrowRight":
    case "ArrowDown":
      nextIndex = (index + 1) % order.length;
      break;
    case "ArrowLeft":
    case "ArrowUp":
      nextIndex = (index - 1 + order.length) % order.length;
      break;
    case "Home":
      nextIndex = 0;
      break;
    case "End":
      nextIndex = order.length - 1;
      break;
    default:
      return;
  }

  event.preventDefault();
  const next = order[nextIndex];
  onChange(next);

  const tablist = event.currentTarget.parentElement;
  tablist
    ?.querySelector<HTMLButtonElement>(`[role="tab"][data-tab-value="${next}"]`)
    ?.focus();
}

import { type ComponentType, type LazyExoticComponent, lazy } from "react";

export function lazyLoad<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
): LazyExoticComponent<T> {
  return lazy(importFn);
}

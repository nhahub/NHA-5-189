import {loadBrowserAssets} from './inference/milestone3.mjs';

let enginePromise;
export function loadEngine() {
  if (!enginePromise) {
    enginePromise = loadBrowserAssets(`${import.meta.env.BASE_URL}models/milestone3/v1/`)
      .catch(error => { enginePromise = undefined; throw error; });
  }
  return enginePromise;
}

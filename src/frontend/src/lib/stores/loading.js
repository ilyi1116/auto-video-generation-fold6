import { writable } from 'svelte/store';

function createLoadingStore() {
  const { subscribe, set, update } = writable({
    isLoading: false,
    text: 'Loading...'
  });

  return {
    subscribe,
    
    // Show loading with optional text
    show: (text = 'Loading...') => {
      set({ isLoading: true, text });
    },
    
    // Hide loading
    hide: () => {
      set({ isLoading: false, text: 'Loading...' });
    },
    
    // Update loading text
    updateText: (text) => {
      update(state => ({ ...state, text }));
    }
  };
}

export const loadingStore = createLoadingStore();
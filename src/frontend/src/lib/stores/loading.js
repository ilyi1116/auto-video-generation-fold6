import { writable } from 'svelte/store';

// Global loading state store
function createLoadingStore() {
  const { subscribe, set, update } = writable({
    isLoading: false,
    message: '',
    progress: null,
    tasks: new Map() // Track multiple async tasks
  });

  return {
    subscribe,
    
    // Show loading with optional message and progress
    show: (message = '載入中...', progress = null) => {
      update(state => ({
        ...state,
        isLoading: true,
        message,
        progress
      }));
    },
    
    // Hide loading
    hide: () => {
      update(state => ({
        ...state,
        isLoading: false,
        message: '',
        progress: null
      }));
    },
    
    // Update loading message or progress
    update: (message, progress = null) => {
      update(state => ({
        ...state,
        message,
        progress
      }));
    },
    
    // Task-based loading management
    startTask: (taskId, message = '載入中...') => {
      update(state => {
        const newTasks = new Map(state.tasks);
        newTasks.set(taskId, { message, startTime: Date.now() });
        
        return {
          ...state,
          isLoading: true,
          message,
          tasks: newTasks
        };
      });
    },
    
    // End specific task
    endTask: (taskId) => {
      update(state => {
        const newTasks = new Map(state.tasks);
        newTasks.delete(taskId);
        
        // If no more tasks, hide loading
        if (newTasks.size === 0) {
          return {
            ...state,
            isLoading: false,
            message: '',
            progress: null,
            tasks: newTasks
          };
        }
        
        // Otherwise, show the most recent task's message
        const remainingTasks = Array.from(newTasks.values());
        const latestTask = remainingTasks[remainingTasks.length - 1];
        
        return {
          ...state,
          message: latestTask.message,
          tasks: newTasks
        };
      });
    },
    
    // Update specific task
    updateTask: (taskId, message, progress = null) => {
      update(state => {
        if (!state.tasks.has(taskId)) {
          return state;
        }
        
        const newTasks = new Map(state.tasks);
        const task = newTasks.get(taskId);
        newTasks.set(taskId, { ...task, message, progress });
        
        return {
          ...state,
          message,
          progress,
          tasks: newTasks
        };
      });
    },
    
    // Clear all tasks
    clearAll: () => {
      set({
        isLoading: false,
        message: '',
        progress: null,
        tasks: new Map()
      });
    }
  };
}

// Error handling store
function createErrorStore() {
  const { subscribe, set, update } = writable({
    errors: [],
    showModal: false,
    currentError: null
  });

  return {
    subscribe,
    
    // Add error
    add: (error) => {
      const errorObj = {
        id: Date.now() + Math.random(),
        message: typeof error === 'string' ? error : error.message || '發生未知錯誤',
        type: error.type || 'error',
        timestamp: new Date(),
        details: error.details || null,
        stack: error.stack || null,
        dismissed: false
      };
      
      update(state => ({
        ...state,
        errors: [...state.errors, errorObj],
        currentError: errorObj,
        showModal: true
      }));
      
      // Auto dismiss after 10 seconds for non-critical errors
      if (errorObj.type !== 'critical') {
        setTimeout(() => {
          update(state => ({
            ...state,
            errors: state.errors.map(e => 
              e.id === errorObj.id ? { ...e, dismissed: true } : e
            )
          }));
        }, 10000);
      }
      
      return errorObj.id;
    },
    
    // Dismiss error
    dismiss: (errorId) => {
      update(state => ({
        ...state,
        errors: state.errors.map(error => 
          error.id === errorId ? { ...error, dismissed: true } : error
        ),
        showModal: false,
        currentError: null
      }));
    },
    
    // Clear all errors
    clear: () => {
      set({
        errors: [],
        showModal: false,
        currentError: null
      });
    },
    
    // Show error modal
    showError: (error) => {
      update(state => ({
        ...state,
        currentError: error,
        showModal: true
      }));
    },
    
    // Hide error modal
    hideModal: () => {
      update(state => ({
        ...state,
        showModal: false,
        currentError: null
      }));
    },
    
    // Get active errors (not dismissed)
    getActive: () => {
      let activeErrors = [];
      update(state => {
        activeErrors = state.errors.filter(error => !error.dismissed);
        return state;
      });
      return activeErrors;
    }
  };
}

// Network status store
function createNetworkStore() {
  const { subscribe, set, update } = writable({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    slowConnection: false,
    connectionType: 'unknown'
  });

  // Monitor network status in browser
  if (typeof window !== 'undefined') {
    const updateOnlineStatus = () => {
      set(state => ({
        ...state,
        isOnline: navigator.onLine
      }));
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Monitor connection speed
    if ('connection' in navigator) {
      const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      
      const updateConnection = () => {
        update(state => ({
          ...state,
          slowConnection: connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g',
          connectionType: connection.effectiveType || 'unknown'
        }));
      };

      connection.addEventListener('change', updateConnection);
      updateConnection();
    }
  }

  return {
    subscribe,
    
    // Manually set online status
    setOnline: (isOnline) => {
      update(state => ({
        ...state,
        isOnline
      }));
    },
    
    // Set slow connection status
    setSlowConnection: (isSlow) => {
      update(state => ({
        ...state,
        slowConnection: isSlow
      }));
    }
  };
}

export const loadingStore = createLoadingStore();
export const errorStore = createErrorStore();
export const networkStore = createNetworkStore();

// Helper function to wrap API calls with loading and error handling
export function withLoading(promise, message = '載入中...', taskId = null) {
  const id = taskId || `task_${Date.now()}_${Math.random()}`;
  
  if (taskId) {
    loadingStore.startTask(id, message);
  } else {
    loadingStore.show(message);
  }
  
  return promise
    .then(result => {
      if (taskId) {
        loadingStore.endTask(id);
      } else {
        loadingStore.hide();
      }
      return result;
    })
    .catch(error => {
      if (taskId) {
        loadingStore.endTask(id);
      } else {
        loadingStore.hide();
      }
      
      errorStore.add({
        message: error.message || '操作失敗',
        type: 'error',
        details: error.details || null,
        stack: error.stack || null
      });
      
      throw error;
    });
}

// Helper to handle async operations with progress
export function withProgress(asyncFunction, message = '處理中...', taskId = null) {
  const id = taskId || `progress_${Date.now()}_${Math.random()}`;
  
  loadingStore.startTask(id, message);
  
  return {
    updateProgress: (progress, newMessage = null) => {
      loadingStore.updateTask(id, newMessage || message, progress);
    },
    
    complete: (result) => {
      loadingStore.endTask(id);
      return result;
    },
    
    error: (error) => {
      loadingStore.endTask(id);
      errorStore.add(error);
      throw error;
    }
  };
}
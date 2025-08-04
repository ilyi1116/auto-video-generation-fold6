import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// 設置測試伺服器
export const server = setupServer(...handlers);
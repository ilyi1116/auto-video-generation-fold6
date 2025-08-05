import "@testing-library/jest-dom";
import { beforeAll, afterAll, afterEach } from "vitest";
import { server } from "./mocks/server";

// 建立 API mocking 在所有測試之前
beforeAll(() => server.listen());

// 在每個測試後重置所有 handler
afterEach(() => server.resetHandlers());

// 在所有測試完成後清理
afterAll(() => server.close());

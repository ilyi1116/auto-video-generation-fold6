/**
 * Button 組件測試套件
 * 測試按鈕組件的渲染、互動和無障礙功能
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import "@testing-library/jest-dom";
import Button from "../../lib/components/ui/Button.svelte";

describe("Button 組件測試", () => {
  describe("基本渲染", () => {
    it("應該正確渲染按鈕文字", () => {
      render(Button, { props: { children: "點擊我" } });

      const button = screen.getByRole("button", { name: "點擊我" });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent("點擊我");
    });

    it("應該渲染空按鈕", () => {
      render(Button);

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent("");
    });

    it("應該正確應用 CSS 類別", () => {
      render(Button, {
        props: {
          children: "測試按鈕",
          class: "custom-class",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("custom-class");
    });
  });

  describe("按鈕變體", () => {
    it("應該正確渲染主要按鈕", () => {
      render(Button, {
        props: {
          variant: "primary",
          children: "主要按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-primary");
    });

    it("應該正確渲染次要按鈕", () => {
      render(Button, {
        props: {
          variant: "secondary",
          children: "次要按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-secondary");
    });

    it("應該正確渲染危險按鈕", () => {
      render(Button, {
        props: {
          variant: "danger",
          children: "危險按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-danger");
    });

    it("應該正確渲染幽靈按鈕", () => {
      render(Button, {
        props: {
          variant: "ghost",
          children: "幽靈按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-ghost");
    });
  });

  describe("按鈕大小", () => {
    it("應該正確渲染小型按鈕", () => {
      render(Button, {
        props: {
          size: "sm",
          children: "小按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-sm");
    });

    it("應該正確渲染普通大小按鈕", () => {
      render(Button, {
        props: {
          size: "md",
          children: "普通按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-md");
    });

    it("應該正確渲染大型按鈕", () => {
      render(Button, {
        props: {
          size: "lg",
          children: "大按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-lg");
    });
  });

  describe("按鈕狀態", () => {
    it("應該正確處理禁用狀態", () => {
      render(Button, {
        props: {
          disabled: true,
          children: "禁用按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveClass("btn-disabled");
    });

    it("應該正確處理載入狀態", () => {
      render(Button, {
        props: {
          loading: true,
          children: "載入中按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveClass("btn-loading");

      // 檢查是否有載入圖示
      const spinner = button.querySelector(".loading-spinner");
      expect(spinner).toBeInTheDocument();
    });

    it("載入狀態時應該隱藏按鈕文字", () => {
      render(Button, {
        props: {
          loading: true,
          children: "載入中按鈕",
        },
      });

      const button = screen.getByRole("button");
      const textElement = button.querySelector(".btn-text");
      expect(textElement).toHaveClass("opacity-0");
    });
  });

  describe("事件處理", () => {
    it("應該正確處理點擊事件", async () => {
      const handleClick = vi.fn();

      render(Button, {
        props: {
          children: "點擊我",
        },
      });

      const button = screen.getByRole("button");

      // 手動綁定事件監聽器
      button.addEventListener("click", handleClick);

      await fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("禁用狀態時不應該觸發點擊事件", async () => {
      const handleClick = vi.fn();

      render(Button, {
        props: {
          disabled: true,
          children: "禁用按鈕",
        },
      });

      const button = screen.getByRole("button");
      button.addEventListener("click", handleClick);

      await fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it("載入狀態時不應該觸發點擊事件", async () => {
      const handleClick = vi.fn();

      render(Button, {
        props: {
          loading: true,
          children: "載入中按鈕",
        },
      });

      const button = screen.getByRole("button");
      button.addEventListener("click", handleClick);

      await fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe("無障礙功能", () => {
    it("應該有正確的 ARIA 標籤", () => {
      render(Button, {
        props: {
          "aria-label": "關閉對話框",
          children: "×",
        },
      });

      const button = screen.getByRole("button", { name: "關閉對話框" });
      expect(button).toBeInTheDocument();
    });

    it("載入狀態時應該有 aria-busy 屬性", () => {
      render(Button, {
        props: {
          loading: true,
          children: "載入中",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-busy", "true");
    });

    it("應該支援鍵盤導航", async () => {
      const handleClick = vi.fn();

      render(Button, {
        props: {
          children: "按鈕",
        },
      });

      const button = screen.getByRole("button");
      button.addEventListener("click", handleClick);

      // 測試 Enter 鍵
      button.focus();
      await fireEvent.keyDown(button, { key: "Enter" });

      expect(handleClick).toHaveBeenCalledTimes(1);

      // 測試 Space 鍵
      await fireEvent.keyDown(button, { key: " " });

      expect(handleClick).toHaveBeenCalledTimes(2);
    });

    it("應該有正確的 tabindex", () => {
      render(Button, {
        props: {
          children: "按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("tabindex", "0");
    });

    it('禁用狀態時應該有 tabindex="-1"', () => {
      render(Button, {
        props: {
          disabled: true,
          children: "禁用按鈕",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("tabindex", "-1");
    });
  });

  describe("圖示支援", () => {
    it("應該正確渲染圖示", () => {
      render(Button, {
        props: {
          icon: "user",
          children: "用戶按鈕",
        },
      });

      const button = screen.getByRole("button");
      const icon = button.querySelector(".btn-icon");
      expect(icon).toBeInTheDocument();
    });

    it("應該支援僅圖示按鈕", () => {
      render(Button, {
        props: {
          icon: "close",
          "aria-label": "關閉",
        },
      });

      const button = screen.getByRole("button", { name: "關閉" });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass("btn-icon-only");
    });

    it("應該正確設置圖示位置", () => {
      render(Button, {
        props: {
          icon: "arrow-right",
          iconPosition: "right",
          children: "下一步",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveClass("btn-icon-right");
    });
  });

  describe("自定義屬性", () => {
    it("應該支援自定義 type 屬性", () => {
      render(Button, {
        props: {
          type: "submit",
          children: "提交",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("type", "submit");
    });

    it("應該支援自定義 name 屬性", () => {
      render(Button, {
        props: {
          name: "action",
          value: "save",
          children: "儲存",
        },
      });

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("name", "action");
      expect(button).toHaveAttribute("value", "save");
    });

    it("應該支援 data 屬性", () => {
      render(Button, {
        props: {
          "data-testid": "my-button",
          "data-action": "delete",
          children: "刪除",
        },
      });

      const button = screen.getByTestId("my-button");
      expect(button).toHaveAttribute("data-action", "delete");
    });
  });
});

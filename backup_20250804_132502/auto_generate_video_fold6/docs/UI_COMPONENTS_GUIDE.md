# UI 組件使用指南

## 📋 組件清單

本項目包含 12 個核心 UI 組件，提供完整的設計系統支援：

### 基礎組件
- **Button** - 多變體按鈕組件
- **Input** - 輸入組件（支援驗證、圖標）
- **Select** - 下拉選擇組件
- **Card** - 卡片容器組件
- **Modal** - 模態對話框組件
- **Badge** - 徽章組件
- **Alert** - 警告/通知組件
- **Tooltip** - 工具提示組件

### 複雜組件
- **Table** - 功能完整的表格組件
- **Tabs** - 標籤頁組件
- **LoadingSpinner** - 載入動畫組件
- **Skeleton** - 骨架屏組件

## 🚀 快速開始

### 1. 導入組件

```javascript
import { Button, Card, Modal, Input } from '$lib/components/ui';
// 或單獨導入
import Button from '$lib/components/ui/Button.svelte';
```

### 2. 基本使用

```svelte
<!-- 按鈕 -->
<Button variant="primary" size="md">
  點擊我
</Button>

<!-- 卡片 -->
<Card>
  <h3 slot="header">標題</h3>
  <p>內容</p>
</Card>
```

## 📚 組件詳細說明

### Button 組件

支援多種變體和狀態的按鈕組件。

```svelte
<script>
  import { Button } from '$lib/components/ui';
  import { Plus, Download } from 'lucide-svelte';
</script>

<!-- 基本按鈕 -->
<Button variant="primary">主要按鈕</Button>
<Button variant="secondary">次要按鈕</Button>
<Button variant="outline">輪廓按鈕</Button>
<Button variant="ghost">幽靈按鈕</Button>
<Button variant="danger">危險按鈕</Button>

<!-- 帶圖標的按鈕 -->
<Button variant="primary" icon={Plus}>新增項目</Button>
<Button variant="outline" icon={Download} iconPosition="right">下載</Button>

<!-- 不同尺寸 -->
<Button size="xs">超小</Button>
<Button size="sm">小</Button>
<Button size="md">中等</Button>
<Button size="lg">大</Button>
<Button size="xl">超大</Button>

<!-- 狀態 -->
<Button loading>載入中...</Button>
<Button disabled>已禁用</Button>
<Button fullWidth>全寬按鈕</Button>

<!-- 作為連結 -->
<Button href="/dashboard" variant="primary">前往儀表板</Button>
```

**Props:**
- `variant`: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success'
- `size`: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
- `disabled`: boolean
- `loading`: boolean
- `fullWidth`: boolean
- `icon`: Svelte component
- `iconPosition`: 'left' | 'right'
- `href`: string (作為連結時使用)

### Input 組件

功能豐富的輸入組件，支援驗證和各種配置。

```svelte
<script>
  import { Input } from '$lib/components/ui';
  import { Mail, Search, Eye } from 'lucide-svelte';
</script>

<!-- 基本輸入 -->
<Input 
  label="電子郵件" 
  type="email" 
  placeholder="請輸入電子郵件"
  required
/>

<!-- 帶圖標的輸入 -->
<Input 
  label="搜尋" 
  icon={Search}
  placeholder="搜尋內容..."
/>

<!-- 可清除的輸入 -->
<Input 
  label="用戶名" 
  clearable
  bind:value={username}
/>

<!-- 錯誤狀態 -->
<Input 
  label="密碼" 
  type="password"
  error="密碼長度至少8位"
/>

<!-- 不同尺寸 -->
<Input size="sm" placeholder="小尺寸" />
<Input size="md" placeholder="中等尺寸" />
<Input size="lg" placeholder="大尺寸" />
```

**Props:**
- `type`: HTML input type
- `value`: string
- `placeholder`: string
- `label`: string
- `error`: string
- `required`: boolean
- `disabled`: boolean
- `readonly`: boolean
- `size`: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
- `icon`: Svelte component
- `iconPosition`: 'left' | 'right'
- `clearable`: boolean

### Select 組件

下拉選擇組件，支援搜尋和自定義選項。

```svelte
<script>
  import { Select } from '$lib/components/ui';
  
  const options = [
    { value: 'apple', label: 'Apple' },
    { value: 'banana', label: 'Banana' },
    { value: 'orange', label: 'Orange' }
  ];
  
  let selectedValue = '';
</script>

<!-- 基本選擇器 -->
<Select 
  {options}
  bind:value={selectedValue}
  placeholder="選擇水果..."
  label="水果選擇"
/>

<!-- 可清除的選擇器 -->
<Select 
  {options}
  bind:value={selectedValue}
  clearable
  label="可清除選擇"
/>

<!-- 錯誤狀態 -->
<Select 
  {options}
  bind:value={selectedValue}
  error="請選擇一個選項"
  required
/>
```

### Card 組件

靈活的卡片容器組件。

```svelte
<script>
  import { Card, Button } from '$lib/components/ui';
</script>

<!-- 基本卡片 -->
<Card>
  <h3 slot="header">卡片標題</h3>
  <p>這是卡片內容。</p>
  <div slot="footer">
    <Button variant="primary">操作</Button>
  </div>
</Card>

<!-- 不同樣式的卡片 -->
<Card hover shadow="lg">
  <p>懸停效果卡片</p>
</Card>

<Card padding="lg" rounded="xl">
  <p>大邊距圓角卡片</p>
</Card>
```

### Modal 組件

功能完整的模態對話框。

```svelte
<script>
  import { Modal, Button } from '$lib/components/ui';
  
  let showModal = false;
</script>

<Button on:click={() => showModal = true}>打開對話框</Button>

<Modal 
  bind:open={showModal}
  title="確認操作"
  size="md"
>
  <p>您確定要執行此操作嗎？</p>
  
  <div slot="footer">
    <Button variant="outline" on:click={() => showModal = false}>
      取消
    </Button>
    <Button variant="danger">
      確認刪除
    </Button>
  </div>
</Modal>
```

### Table 組件

功能豐富的表格組件，支援排序、選擇、分頁。

```svelte
<script>
  import { Table, Badge } from '$lib/components/ui';
  
  const columns = [
    { key: 'name', title: '姓名', sortable: true },
    { key: 'email', title: '電子郵件', sortable: true },
    { key: 'status', title: '狀態', component: StatusBadge },
    { key: 'actions', title: '操作', component: ActionButtons }
  ];
  
  const data = [
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' }
  ];
</script>

<Table 
  {columns}
  {data}
  sortable
  selectable
  hoverable
  on:sort={handleSort}
  on:select={handleSelection}
  on:rowClick={handleRowClick}
/>
```

### Alert 組件

不同類型的警告和通知組件。

```svelte
<script>
  import { Alert } from '$lib/components/ui';
</script>

<!-- 不同變體的警告 -->
<Alert variant="success" title="成功！">
  操作已成功完成。
</Alert>

<Alert variant="warning" title="注意">
  這是一個警告消息。
</Alert>

<Alert variant="danger" title="錯誤" dismissible on:dismiss={handleDismiss}>
  發生了一個錯誤，請重試。
</Alert>

<Alert variant="info">
  這是一個信息提示。
</Alert>
```

### Tabs 組件

標籤頁組件，支援多種樣式。

```svelte
<script>
  import { Tabs } from '$lib/components/ui';
  import { User, Settings, Bell } from 'lucide-svelte';
  
  const tabs = [
    { id: 'profile', label: '個人資料', icon: User },
    { id: 'settings', label: '設定', icon: Settings, badge: '3' },
    { id: 'notifications', label: '通知', icon: Bell }
  ];
  
  let activeTab = 'profile';
</script>

<!-- 默認樣式 -->
<Tabs {tabs} bind:activeTab>
  {#if activeTab === 'profile'}
    <p>個人資料內容</p>
  {:else if activeTab === 'settings'}
    <p>設定內容</p>
  {:else if activeTab === 'notifications'}
    <p>通知內容</p>
  {/if}
</Tabs>

<!-- 藥丸樣式 -->
<Tabs {tabs} bind:activeTab variant="pills" />

<!-- 下劃線樣式 -->
<Tabs {tabs} bind:activeTab variant="underline" />
```

### Loading 組件

載入狀態相關組件。

```svelte
<script>
  import { LoadingSpinner, Skeleton } from '$lib/components/ui';
</script>

<!-- 載入動畫 -->
<LoadingSpinner size="lg" text="載入中..." />

<!-- 全螢幕載入 -->
<LoadingSpinner fullscreen text="正在處理..." />

<!-- 骨架屏 -->
<Skeleton width="100%" height="2rem" />
<Skeleton width="75%" height="1rem" />

<!-- 卡片骨架屏 -->
<Skeleton>
  <div slot="card">
    <!-- 自定義骨架屏內容 -->
  </div>
</Skeleton>
```

### Tooltip 組件

工具提示組件。

```svelte
<script>
  import { Tooltip, Button } from '$lib/components/ui';
</script>

<Tooltip content="這是一個提示">
  <Button>懸停查看提示</Button>
</Tooltip>

<!-- 不同位置 -->
<Tooltip content="頂部提示" placement="top">
  <span>頂部</span>
</Tooltip>

<Tooltip content="右側提示" placement="right">
  <span>右側</span>
</Tooltip>
```

## 🎨 主題定制

所有組件都支援深色模式和主題定制：

```css
/* 在 app.css 中自定義主題色彩 */
:root {
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
}
```

## 📱 響應式設計

所有組件都已優化為響應式設計：

```svelte
<!-- 響應式按鈕 -->
<Button fullWidth class="sm:w-auto">
  移動端全寬，桌面端自適應
</Button>

<!-- 響應式表格 -->
<Table compact class="hidden md:block" />
```

## 🔧 自定義樣式

可以通過 class 屬性添加自定義樣式：

```svelte
<Button class="custom-button-style">
  自定義按鈕
</Button>

<Card class="shadow-2xl border-2 border-primary-200">
  自定義卡片
</Card>
```

## 📋 最佳實踐

### 1. 一致性
保持整個應用中組件使用的一致性：

```svelte
<!-- 好的做法 -->
<Button variant="primary" size="md">主要操作</Button>
<Button variant="outline" size="md">次要操作</Button>

<!-- 避免 -->
<Button variant="primary" size="lg">主要操作</Button>
<Button variant="outline" size="sm">次要操作</Button>
```

### 2. 可訪問性
確保組件具有適當的可訪問性屬性：

```svelte
<Button aria-label="關閉對話框">
  <X />
</Button>

<Input 
  label="電子郵件"
  aria-describedby="email-error"
  error="請輸入有效的電子郵件"
/>
```

### 3. 錯誤處理
適當處理組件的錯誤狀態：

```svelte
<Input 
  bind:value={email}
  error={emailError}
  on:input={validateEmail}
/>

<Alert variant="danger" dismissible>
  {errorMessage}
</Alert>
```

## 🚀 進階使用

### 組合組件
組合多個組件創建複雜界面：

```svelte
<Card>
  <div slot="header">
    <Tabs {tabs} bind:activeTab />
  </div>
  
  <div class="p-6">
    {#if loading}
      <LoadingSpinner />
    {:else}
      <Table {columns} {data} />
    {/if}
  </div>
  
  <div slot="footer">
    <Button variant="primary">保存</Button>
  </div>
</Card>
```

### 自定義 Hook 集成
與自定義 Hook 結合使用：

```svelte
<script>
  import { useForm, validators } from '$lib/hooks';
  import { Input, Button, Alert } from '$lib/components/ui';
  
  const { values, errors, handleSubmit } = useForm(
    { email: '', password: '' },
    {
      email: [validators.required(), validators.email()],
      password: [validators.required(), validators.minLength(8)]
    }
  );
</script>

<form on:submit={handleSubmit(onSubmit)}>
  <Input 
    label="電子郵件"
    bind:value={$values.email}
    error={$errors.email}
  />
  
  <Input 
    label="密碼"
    type="password"
    bind:value={$values.password}
    error={$errors.password}
  />
  
  <Button type="submit" loading={$isSubmitting}>
    登入
  </Button>
</form>
```

這個組件庫提供了構建現代 Web 應用所需的所有基礎組件，具有優秀的用戶體驗、完整的功能和高度的可定制性。
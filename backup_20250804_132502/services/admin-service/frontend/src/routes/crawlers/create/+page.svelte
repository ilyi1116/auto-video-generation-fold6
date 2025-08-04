<script lang="ts">
	import { goto } from '$app/navigation';
	import { apiClient } from '$utils/api';
	import { toast } from 'svelte-french-toast';
	import { 
		Save, 
		ArrowLeft, 
		Plus, 
		X, 
		Globe, 
		Tag, 
		Clock, 
		Settings, 
		Info,
		ChevronDown 
	} from 'lucide-svelte';

	interface CrawlerConfigForm {
		name: string;
		description: string;
		target_url: string;
		keywords: string[];
		css_selectors: Record<string, string>;
		headers: Record<string, string>;
		schedule_type: string;
		schedule_config: Record<string, any>;
		status: string;
		max_pages: number;
		delay_seconds: number;
		retry_attempts: number;
		timeout_seconds: number;
		use_proxy: boolean;
		proxy_config: Record<string, string>;
	}

	let form: CrawlerConfigForm = {
		name: '',
		description: '',
		target_url: '',
		keywords: [],
		css_selectors: {},
		headers: {},
		schedule_type: 'daily',
		schedule_config: {},
		status: 'active',
		max_pages: 10,
		delay_seconds: 1,
		retry_attempts: 3,
		timeout_seconds: 30,
		use_proxy: false,
		proxy_config: {}
	};

	let loading = false;
	let errors: Record<string, string> = {};

	// 新關鍵字輸入
	let newKeyword = '';

	// 新 CSS 選擇器
	let newSelectorName = '';
	let newSelectorValue = '';

	// 新請求頭
	let newHeaderName = '';
	let newHeaderValue = '';

	// 代理配置
	let newProxyKey = '';
	let newProxyValue = '';

	// 排程配置
	let cronExpression = '';
	let scheduleHour = 0;
	let scheduleMinute = 0;
	let weekDay = 1;
	let monthDay = 1;

	// 狀態選項
	const statusOptions = [
		{ value: 'active', label: '啟用' },
		{ value: 'inactive', label: '停用' },
		{ value: 'paused', label: '暫停' }
	];

	// 排程類型選項
	const scheduleTypeOptions = [
		{ value: 'once', label: '單次執行' },
		{ value: 'hourly', label: '每小時' },
		{ value: 'daily', label: '每日' },
		{ value: 'weekly', label: '每週' },
		{ value: 'monthly', label: '每月' },
		{ value: 'custom_cron', label: '自定義 Cron' }
	];

	// 添加關鍵字
	function addKeyword() {
		if (newKeyword.trim() && !form.keywords.includes(newKeyword.trim())) {
			form.keywords = [...form.keywords, newKeyword.trim()];
			newKeyword = '';
		}
	}

	// 移除關鍵字
	function removeKeyword(index: number) {
		form.keywords = form.keywords.filter((_, i) => i !== index);
	}

	// 添加 CSS 選擇器
	function addSelector() {
		if (newSelectorName.trim() && newSelectorValue.trim()) {
			form.css_selectors[newSelectorName.trim()] = newSelectorValue.trim();
			form.css_selectors = { ...form.css_selectors };
			newSelectorName = '';
			newSelectorValue = '';
		}
	}

	// 移除 CSS 選擇器
	function removeSelector(key: string) {
		delete form.css_selectors[key];
		form.css_selectors = { ...form.css_selectors };
	}

	// 添加請求頭
	function addHeader() {
		if (newHeaderName.trim() && newHeaderValue.trim()) {
			form.headers[newHeaderName.trim()] = newHeaderValue.trim();
			form.headers = { ...form.headers };
			newHeaderName = '';
			newHeaderValue = '';
		}
	}

	// 移除請求頭
	function removeHeader(key: string) {
		delete form.headers[key];
		form.headers = { ...form.headers };
	}

	// 添加代理配置
	function addProxyConfig() {
		if (newProxyKey.trim() && newProxyValue.trim()) {
			form.proxy_config[newProxyKey.trim()] = newProxyValue.trim();
			form.proxy_config = { ...form.proxy_config };
			newProxyKey = '';
			newProxyValue = '';
		}
	}

	// 移除代理配置
	function removeProxyConfig(key: string) {
		delete form.proxy_config[key];
		form.proxy_config = { ...form.proxy_config };
	}

	// 處理排程配置變更
	function updateScheduleConfig() {
		switch (form.schedule_type) {
			case 'hourly':
				form.schedule_config = { minute: scheduleMinute };
				break;
			case 'daily':
				form.schedule_config = { hour: scheduleHour, minute: scheduleMinute };
				break;
			case 'weekly':
				form.schedule_config = { 
					day_of_week: weekDay, 
					hour: scheduleHour, 
					minute: scheduleMinute 
				};
				break;
			case 'monthly':
				form.schedule_config = { 
					day_of_month: monthDay, 
					hour: scheduleHour, 
					minute: scheduleMinute 
				};
				break;
			case 'custom_cron':
				form.schedule_config = { cron: cronExpression };
				break;
			default:
				form.schedule_config = {};
		}
	}

	// 表單驗證
	function validateForm(): boolean {
		errors = {};

		if (!form.name.trim()) {
			errors.name = '請輸入爬蟲名稱';
		}

		if (!form.target_url.trim()) {
			errors.target_url = '請輸入目標網址';
		} else if (!isValidUrl(form.target_url)) {
			errors.target_url = '請輸入有效的網址';
		}

		if (form.keywords.length === 0) {
			errors.keywords = '請至少添加一個關鍵字';
		}

		if (form.schedule_type === 'custom_cron' && !cronExpression.trim()) {
			errors.cron = '請輸入 Cron 表達式';
		}

		if (form.max_pages < 1 || form.max_pages > 1000) {
			errors.max_pages = '最大頁數必須在 1-1000 之間';
		}

		if (form.delay_seconds < 0 || form.delay_seconds > 60) {
			errors.delay_seconds = '延遲秒數必須在 0-60 之間';
		}

		if (form.retry_attempts < 0 || form.retry_attempts > 10) {
			errors.retry_attempts = '重試次數必須在 0-10 之間';
		}

		if (form.timeout_seconds < 1 || form.timeout_seconds > 300) {
			errors.timeout_seconds = '超時時間必須在 1-300 之間';
		}

		return Object.keys(errors).length === 0;
	}

	// 網址驗證
	function isValidUrl(url: string): boolean {
		try {
			new URL(url);
			return true;
		} catch {
			return false;
		}
	}

	// 提交表單
	async function handleSubmit() {
		if (!validateForm()) {
			toast.error('請修正表單錯誤');
			return;
		}

		try {
			loading = true;
			updateScheduleConfig();

			const response = await apiClient.crawlers.create(form);
			if (response.data.success) {
				toast.success('爬蟲配置創建成功');
				goto('/crawlers');
			} else {
				toast.error(response.data.message || '創建失敗');
			}
		} catch (error) {
			console.error('創建失敗:', error);
			toast.error('創建失敗');
		} finally {
			loading = false;
		}
	}

	// 取消並返回
	function handleCancel() {
		goto('/crawlers');
	}

	// 處理關鍵字輸入的 Enter 鍵
	function handleKeywordKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addKeyword();
		}
	}

	// 更新排程配置
	$: if (form.schedule_type) {
		updateScheduleConfig();
	}
</script>

<svelte:head>
	<title>新增爬蟲 - 後台管理系統</title>
</svelte:head>

<div class="max-w-4xl mx-auto space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center">
		<button
			on:click={handleCancel}
			class="mr-4 p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
		>
			<ArrowLeft class="w-5 h-5" />
		</button>
		<div>
			<h1 class="text-2xl font-bold text-gray-900">新增爬蟲配置</h1>
			<p class="mt-2 text-gray-600">配置網站爬蟲的基本信息和抓取規則</p>
		</div>
	</div>

	<form on:submit|preventDefault={handleSubmit} class="space-y-6">
		<!-- 基本信息 -->
		<div class="card">
			<div class="flex items-center mb-4">
				<Info class="w-5 h-5 text-blue-600 mr-2" />
				<h2 class="text-lg font-medium text-gray-900">基本信息</h2>
			</div>
			
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<div>
					<label for="name" class="block text-sm font-medium text-gray-700 mb-1">
						爬蟲名稱 <span class="text-red-500">*</span>
					</label>
					<input
						id="name"
						type="text"
						bind:value={form.name}
						class="form-input {errors.name ? 'border-red-300' : ''}"
						placeholder="輸入爬蟲名稱"
					/>
					{#if errors.name}
						<p class="mt-1 text-sm text-red-600">{errors.name}</p>
					{/if}
				</div>

				<div>
					<label for="status" class="block text-sm font-medium text-gray-700 mb-1">
						狀態
					</label>
					<div class="relative">
						<select
							id="status"
							bind:value={form.status}
							class="form-select"
						>
							{#each statusOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
						<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
					</div>
				</div>

				<div class="lg:col-span-2">
					<label for="description" class="block text-sm font-medium text-gray-700 mb-1">
						描述
					</label>
					<textarea
						id="description"
						bind:value={form.description}
						rows="3"
						class="form-textarea"
						placeholder="輸入爬蟲描述（可選）"
					></textarea>
				</div>

				<div class="lg:col-span-2">
					<label for="target_url" class="block text-sm font-medium text-gray-700 mb-1">
						目標網址 <span class="text-red-500">*</span>
					</label>
					<div class="relative">
						<Globe class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
						<input
							id="target_url"
							type="url"
							bind:value={form.target_url}
							class="form-input pl-10 {errors.target_url ? 'border-red-300' : ''}"
							placeholder="https://example.com"
						/>
					</div>
					{#if errors.target_url}
						<p class="mt-1 text-sm text-red-600">{errors.target_url}</p>
					{/if}
				</div>
			</div>
		</div>

		<!-- 關鍵字配置 -->
		<div class="card">
			<div class="flex items-center mb-4">
				<Tag class="w-5 h-5 text-green-600 mr-2" />
				<h2 class="text-lg font-medium text-gray-900">關鍵字配置</h2>
			</div>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">
						搜索關鍵字 <span class="text-red-500">*</span>
					</label>
					<div class="flex space-x-2">
						<input
							type="text"
							bind:value={newKeyword}
							on:keydown={handleKeywordKeydown}
							class="form-input flex-1"
							placeholder="輸入關鍵字後按 Enter 或點擊添加"
						/>
						<button
							type="button"
							on:click={addKeyword}
							class="btn btn-outline"
						>
							<Plus class="w-4 h-4" />
						</button>
					</div>
					{#if errors.keywords}
						<p class="mt-1 text-sm text-red-600">{errors.keywords}</p>
					{/if}
				</div>

				{#if form.keywords.length > 0}
					<div class="flex flex-wrap gap-2">
						{#each form.keywords as keyword, index}
							<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
								{keyword}
								<button
									type="button"
									on:click={() => removeKeyword(index)}
									class="ml-2 text-blue-600 hover:text-blue-800"
								>
									<X class="w-3 h-3" />
								</button>
							</span>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- CSS 選擇器配置 -->
		<div class="card">
			<div class="flex items-center mb-4">
				<Settings class="w-5 h-5 text-purple-600 mr-2" />
				<h2 class="text-lg font-medium text-gray-900">CSS 選擇器配置</h2>
			</div>

			<div class="space-y-4">
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
					<input
						type="text"
						bind:value={newSelectorName}
						class="form-input"
						placeholder="選擇器名稱（如：title）"
					/>
					<input
						type="text"
						bind:value={newSelectorValue}
						class="form-input"
						placeholder="CSS 選擇器（如：h1.title）"
					/>
					<button
						type="button"
						on:click={addSelector}
						class="btn btn-outline"
					>
						<Plus class="w-4 h-4 mr-2" />
						添加選擇器
					</button>
				</div>

				{#if Object.keys(form.css_selectors).length > 0}
					<div class="space-y-2">
						{#each Object.entries(form.css_selectors) as [name, selector]}
							<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
								<div>
									<span class="font-medium text-gray-900">{name}:</span>
									<span class="text-gray-600 ml-2">{selector}</span>
								</div>
								<button
									type="button"
									on:click={() => removeSelector(name)}
									class="text-red-600 hover:text-red-800"
								>
									<X class="w-4 h-4" />
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- 排程配置 -->
		<div class="card">
			<div class="flex items-center mb-4">
				<Clock class="w-5 h-5 text-orange-600 mr-2" />
				<h2 class="text-lg font-medium text-gray-900">排程配置</h2>
			</div>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 mb-1">
						排程類型
					</label>
					<div class="relative">
						<select
							bind:value={form.schedule_type}
							class="form-select"
						>
							{#each scheduleTypeOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
						<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
					</div>
				</div>

				{#if form.schedule_type === 'hourly'}
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">
							執行分鐘
						</label>
						<input
							type="number"
							bind:value={scheduleMinute}
							min="0"
							max="59"
							class="form-input"
							placeholder="0-59"
						/>
					</div>
				{:else if form.schedule_type === 'daily'}
					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行小時
							</label>
							<input
								type="number"
								bind:value={scheduleHour}
								min="0"
								max="23"
								class="form-input"
								placeholder="0-23"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行分鐘
							</label>
							<input
								type="number"
								bind:value={scheduleMinute}
								min="0"
								max="59"
								class="form-input"
								placeholder="0-59"
							/>
						</div>
					</div>
				{:else if form.schedule_type === 'weekly'}
					<div class="grid grid-cols-3 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								星期幾
							</label>
							<select bind:value={weekDay} class="form-select">
								<option value={1}>星期一</option>
								<option value={2}>星期二</option>
								<option value={3}>星期三</option>
								<option value={4}>星期四</option>
								<option value={5}>星期五</option>
								<option value={6}>星期六</option>
								<option value={0}>星期日</option>
							</select>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行小時
							</label>
							<input
								type="number"
								bind:value={scheduleHour}
								min="0"
								max="23"
								class="form-input"
								placeholder="0-23"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行分鐘
							</label>
							<input
								type="number"
								bind:value={scheduleMinute}
								min="0"
								max="59"
								class="form-input"
								placeholder="0-59"
							/>
						</div>
					</div>
				{:else if form.schedule_type === 'monthly'}
					<div class="grid grid-cols-3 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								每月第幾天
							</label>
							<input
								type="number"
								bind:value={monthDay}
								min="1"
								max="31"
								class="form-input"
								placeholder="1-31"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行小時
							</label>
							<input
								type="number"
								bind:value={scheduleHour}
								min="0"
								max="23"
								class="form-input"
								placeholder="0-23"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">
								執行分鐘
							</label>
							<input
								type="number"
								bind:value={scheduleMinute}
								min="0"
								max="59"
								class="form-input"
								placeholder="0-59"
							/>
						</div>
					</div>
				{:else if form.schedule_type === 'custom_cron'}
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">
							Cron 表達式
						</label>
						<input
							type="text"
							bind:value={cronExpression}
							class="form-input {errors.cron ? 'border-red-300' : ''}"
							placeholder="例如：0 0 * * * （每天午夜執行）"
						/>
						{#if errors.cron}
							<p class="mt-1 text-sm text-red-600">{errors.cron}</p>
						{/if}
						<p class="mt-1 text-sm text-gray-500">
							格式：秒 分 時 日 月 星期
						</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- 高級配置 -->
		<div class="card">
			<div class="flex items-center mb-4">
				<Settings class="w-5 h-5 text-gray-600 mr-2" />
				<h2 class="text-lg font-medium text-gray-900">高級配置</h2>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<div>
					<label for="max_pages" class="block text-sm font-medium text-gray-700 mb-1">
						最大頁數
					</label>
					<input
						id="max_pages"
						type="number"
						bind:value={form.max_pages}
						min="1"
						max="1000"
						class="form-input {errors.max_pages ? 'border-red-300' : ''}"
					/>
					{#if errors.max_pages}
						<p class="mt-1 text-sm text-red-600">{errors.max_pages}</p>
					{/if}
				</div>

				<div>
					<label for="delay_seconds" class="block text-sm font-medium text-gray-700 mb-1">
						延遲秒數
					</label>
					<input
						id="delay_seconds"
						type="number"
						bind:value={form.delay_seconds}
						min="0"
						max="60"
						class="form-input {errors.delay_seconds ? 'border-red-300' : ''}"
					/>
					{#if errors.delay_seconds}
						<p class="mt-1 text-sm text-red-600">{errors.delay_seconds}</p>
					{/if}
				</div>

				<div>
					<label for="retry_attempts" class="block text-sm font-medium text-gray-700 mb-1">
						重試次數
					</label>
					<input
						id="retry_attempts"
						type="number"
						bind:value={form.retry_attempts}
						min="0"
						max="10"
						class="form-input {errors.retry_attempts ? 'border-red-300' : ''}"
					/>
					{#if errors.retry_attempts}
						<p class="mt-1 text-sm text-red-600">{errors.retry_attempts}</p>
					{/if}
				</div>

				<div>
					<label for="timeout_seconds" class="block text-sm font-medium text-gray-700 mb-1">
						超時時間（秒）
					</label>
					<input
						id="timeout_seconds"
						type="number"
						bind:value={form.timeout_seconds}
						min="1"
						max="300"
						class="form-input {errors.timeout_seconds ? 'border-red-300' : ''}"
					/>
					{#if errors.timeout_seconds}
						<p class="mt-1 text-sm text-red-600">{errors.timeout_seconds}</p>
					{/if}
				</div>
			</div>

			<!-- 請求頭配置 -->
			<div class="mt-6">
				<h3 class="text-md font-medium text-gray-900 mb-3">HTTP 請求頭</h3>
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-3">
					<input
						type="text"
						bind:value={newHeaderName}
						class="form-input"
						placeholder="請求頭名稱（如：User-Agent）"
					/>
					<input
						type="text"
						bind:value={newHeaderValue}
						class="form-input"
						placeholder="請求頭值"
					/>
					<button
						type="button"
						on:click={addHeader}
						class="btn btn-outline"
					>
						<Plus class="w-4 h-4 mr-2" />
						添加請求頭
					</button>
				</div>

				{#if Object.keys(form.headers).length > 0}
					<div class="space-y-2">
						{#each Object.entries(form.headers) as [name, value]}
							<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
								<div>
									<span class="font-medium text-gray-900">{name}:</span>
									<span class="text-gray-600 ml-2">{value}</span>
								</div>
								<button
									type="button"
									on:click={() => removeHeader(name)}
									class="text-red-600 hover:text-red-800"
								>
									<X class="w-4 h-4" />
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- 代理配置 -->
			<div class="mt-6">
				<div class="flex items-center space-x-3 mb-3">
					<input
						id="use_proxy"
						type="checkbox"
						bind:checked={form.use_proxy}
						class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
					/>
					<label for="use_proxy" class="text-md font-medium text-gray-900">
						使用代理服務器
					</label>
				</div>

				{#if form.use_proxy}
					<div class="space-y-4">
						<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
							<input
								type="text"
								bind:value={newProxyKey}
								class="form-input"
								placeholder="配置項（如：host, port）"
							/>
							<input
								type="text"
								bind:value={newProxyValue}
								class="form-input"
								placeholder="配置值"
							/>
							<button
								type="button"
								on:click={addProxyConfig}
								class="btn btn-outline"
							>
								<Plus class="w-4 h-4 mr-2" />
								添加配置
							</button>
						</div>

						{#if Object.keys(form.proxy_config).length > 0}
							<div class="space-y-2">
								{#each Object.entries(form.proxy_config) as [key, value]}
									<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
										<div>
											<span class="font-medium text-gray-900">{key}:</span>
											<span class="text-gray-600 ml-2">{value}</span>
										</div>
										<button
											type="button"
											on:click={() => removeProxyConfig(key)}
											class="text-red-600 hover:text-red-800"
										>
											<X class="w-4 h-4" />
										</button>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- 提交按鈕 -->
		<div class="flex justify-end space-x-3">
			<button
				type="button"
				on:click={handleCancel}
				class="btn btn-outline"
			>
				取消
			</button>
			<button
				type="submit"
				disabled={loading}
				class="btn btn-primary"
			>
				{#if loading}
					<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
				{:else}
					<Save class="w-4 h-4 mr-2" />
				{/if}
				創建爬蟲
			</button>
		</div>
	</form>
</div>
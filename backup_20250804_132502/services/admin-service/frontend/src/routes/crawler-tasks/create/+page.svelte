<script lang="ts">
	import { goto } from '$app/navigation';
	import { apiClient } from '$utils/api';
	import { toast } from 'svelte-french-toast';
	import { 
		ArrowLeft, 
		Save, 
		Plus, 
		X,
		Clock,
		Target,
		Tag,
		Settings
	} from 'lucide-svelte';

	interface CrawlerTaskForm {
		task_name: string;
		keywords: string[];
		target_url: string;
		schedule_type: 'daily' | 'weekly' | 'hourly' | 'cron';
		schedule_time: string;
		is_active: boolean;
	}

	let form: CrawlerTaskForm = {
		task_name: '',
		keywords: [],
		target_url: '',
		schedule_type: 'daily',
		schedule_time: '',
		is_active: true
	};

	let keywordInput = '';
	let saving = false;
	let errors: Record<string, string> = {};

	// 排程類型選項
	const scheduleOptions = [
		{ value: 'daily', label: '每日', description: '每天執行一次' },
		{ value: 'weekly', label: '每週', description: '每週執行一次' },
		{ value: 'hourly', label: '每小時', description: '每小時執行一次' },
		{ value: 'cron', label: '自定義 Cron', description: '使用 Cron 表達式' }
	];

	// 添加關鍵字
	function addKeyword() {
		const keyword = keywordInput.trim();
		if (keyword && !form.keywords.includes(keyword)) {
			form.keywords = [...form.keywords, keyword];
			keywordInput = '';
		}
	}

	// 移除關鍵字
	function removeKeyword(keyword: string) {
		form.keywords = form.keywords.filter(k => k !== keyword);
	}

	// 處理關鍵字輸入
	function handleKeywordInput(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addKeyword();
		}
	}

	// 驗證表單
	function validateForm(): boolean {
		errors = {};

		if (!form.task_name.trim()) {
			errors.task_name = '任務名稱為必填項';
		}

		if (form.keywords.length === 0) {
			errors.keywords = '至少需要一個關鍵字';
		}

		if (form.schedule_type === 'cron' && !form.schedule_time.trim()) {
			errors.schedule_time = 'Cron 表達式為必填項';
		}

		return Object.keys(errors).length === 0;
	}

	// 提交表單
	async function handleSubmit() {
		if (!validateForm()) {
			return;
		}

		try {
			saving = true;
			
			const payload = {
				...form,
				target_url: form.target_url.trim() || null,
				schedule_time: form.schedule_time.trim() || null
			};

			const response = await apiClient.crawlerTasks.create(payload);
			
			if (response.data.success) {
				toast.success('爬蟲任務創建成功');
				goto('/crawler-tasks');
			} else {
				toast.error(response.data.message || '創建失敗');
			}
		} catch (error) {
			console.error('創建失敗:', error);
			toast.error('創建失敗');
		} finally {
			saving = false;
		}
	}

	// 取消
	function handleCancel() {
		goto('/crawler-tasks');
	}

	// 根據排程類型顯示不同的時間輸入提示
	function getScheduleTimeHelper(type: string): string {
		switch (type) {
			case 'daily':
				return '例如: 09:00 (每天上午9點執行)';
			case 'weekly':
				return '例如: MON 09:00 (每週一上午9點執行)';
			case 'hourly':
				return '例如: :30 (每小時的30分執行)';
			case 'cron':
				return '例如: 0 9 * * 1 (每週一上午9點執行)';
			default:
				return '';
		}
	}
</script>

<svelte:head>
	<title>新增爬蟲任務 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center justify-between">
		<div class="flex items-center space-x-4">
			<button
				on:click={handleCancel}
				class="btn btn-outline btn-sm"
			>
				<ArrowLeft class="w-4 h-4 mr-2" />
				返回
			</button>
			<div>
				<h1 class="text-2xl font-bold text-gray-900">新增爬蟲任務</h1>
				<p class="mt-2 text-gray-600">創建新的爬蟲任務，設定關鍵字、目標網址和執行排程</p>
			</div>
		</div>
	</div>

	<!-- 表單 -->
	<form on:submit|preventDefault={handleSubmit} class="space-y-6">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- 左側：基本信息 -->
			<div class="lg:col-span-2 space-y-6">
				<!-- 任務基本信息 -->
				<div class="card">
					<div class="flex items-center mb-4">
						<Settings class="w-5 h-5 text-gray-600 mr-2" />
						<h2 class="text-lg font-medium text-gray-900">基本信息</h2>
					</div>

					<div class="space-y-4">
						<!-- 任務名稱 -->
						<div>
							<label for="task_name" class="form-label">任務名稱 <span class="text-red-500">*</span></label>
							<input
								id="task_name"
								type="text"
								bind:value={form.task_name}
								class="form-input {errors.task_name ? 'border-red-300' : ''}"
								placeholder="輸入任務名稱"
								required
							/>
							{#if errors.task_name}
								<p class="mt-1 text-sm text-red-600">{errors.task_name}</p>
							{/if}
						</div>

						<!-- 目標網址 -->
						<div>
							<label for="target_url" class="form-label">目標網址 <span class="text-gray-500">(可選)</span></label>
							<div class="relative">
								<Target class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
								<input
									id="target_url"
									type="url"
									bind:value={form.target_url}
									class="form-input pl-10"
									placeholder="https://example.com"
								/>
							</div>
							<p class="mt-1 text-xs text-gray-500">如果留空，將使用通用爬蟲策略</p>
						</div>

						<!-- 狀態 -->
						<div>
							<label class="flex items-center">
								<input
									type="checkbox"
									bind:checked={form.is_active}
									class="form-checkbox"
								/>
								<span class="ml-2 text-sm text-gray-700">啟用任務</span>
							</label>
							<p class="mt-1 text-xs text-gray-500">未勾選時任務將不會自動執行</p>
						</div>
					</div>
				</div>

				<!-- 關鍵字設定 -->
				<div class="card">
					<div class="flex items-center mb-4">
						<Tag class="w-5 h-5 text-gray-600 mr-2" />
						<h2 class="text-lg font-medium text-gray-900">關鍵字設定</h2>
					</div>

					<div class="space-y-4">
						<!-- 關鍵字輸入 -->
						<div>
							<label for="keyword_input" class="form-label">添加關鍵字 <span class="text-red-500">*</span></label>
							<div class="flex">
								<input
									id="keyword_input"
									type="text"
									bind:value={keywordInput}
									on:keydown={handleKeywordInput}
									class="form-input rounded-r-none"
									placeholder="輸入關鍵字並按 Enter"
								/>
								<button
									type="button"
									on:click={addKeyword}
									class="btn btn-outline rounded-l-none border-l-0"
								>
									<Plus class="w-4 h-4" />
								</button>
							</div>
							{#if errors.keywords}
								<p class="mt-1 text-sm text-red-600">{errors.keywords}</p>
							{/if}
						</div>

						<!-- 關鍵字列表 -->
						{#if form.keywords.length > 0}
							<div>
								<label class="form-label">已添加的關鍵字 ({form.keywords.length})</label>
								<div class="flex flex-wrap gap-2 mt-2">
									{#each form.keywords as keyword}
										<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
											{keyword}
											<button
												type="button"
												on:click={() => removeKeyword(keyword)}
												class="ml-2 hover:text-blue-600"
											>
												<X class="w-3 h-3" />
											</button>
										</span>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- 右側：排程設定 -->
			<div class="space-y-6">
				<div class="card">
					<div class="flex items-center mb-4">
						<Clock class="w-5 h-5 text-gray-600 mr-2" />
						<h2 class="text-lg font-medium text-gray-900">排程設定</h2>
					</div>

					<div class="space-y-4">
						<!-- 排程類型 -->
						<div>
							<label class="form-label">排程類型</label>
							<div class="space-y-2">
								{#each scheduleOptions as option}
									<label class="flex items-start">
										<input
											type="radio"
											bind:group={form.schedule_type}
											value={option.value}
											class="form-radio mt-1"
										/>
										<div class="ml-2">
											<div class="text-sm font-medium text-gray-900">{option.label}</div>
											<div class="text-xs text-gray-500">{option.description}</div>
										</div>
									</label>
								{/each}
							</div>
						</div>

						<!-- 排程時間 -->
						<div>
							<label for="schedule_time" class="form-label">
								排程時間
								{#if form.schedule_type === 'cron'}
									<span class="text-red-500">*</span>
								{/if}
							</label>
							<input
								id="schedule_time"
								type="text"
								bind:value={form.schedule_time}
								class="form-input {errors.schedule_time ? 'border-red-300' : ''}"
								placeholder={getScheduleTimeHelper(form.schedule_type)}
							/>
							{#if errors.schedule_time}
								<p class="mt-1 text-sm text-red-600">{errors.schedule_time}</p>
							{:else}
								<p class="mt-1 text-xs text-gray-500">{getScheduleTimeHelper(form.schedule_type)}</p>
							{/if}
						</div>

						<!-- 排程說明 -->
						<div class="bg-blue-50 border border-blue-200 rounded-md p-3">
							<div class="text-sm text-blue-800">
								<p class="font-medium mb-1">排程說明：</p>
								{#if form.schedule_type === 'daily'}
									<p>任務將每天在指定時間執行一次</p>
								{:else if form.schedule_type === 'weekly'}
									<p>任務將每週在指定日期和時間執行一次</p>
								{:else if form.schedule_type === 'hourly'}
									<p>任務將每小時在指定分鐘執行一次</p>
								{:else if form.schedule_type === 'cron'}
									<p>使用標準 Cron 表達式設定執行時間</p>
									<p class="text-xs mt-1">格式: 分 時 日 月 週</p>
								{/if}
							</div>
						</div>
					</div>
				</div>

				<!-- 操作按鈕 -->
				<div class="card">
					<div class="space-y-3">
						<button
							type="submit"
							disabled={saving}
							class="btn btn-primary w-full"
						>
							<Save class="w-4 h-4 mr-2" />
							{saving ? '創建中...' : '創建任務'}
						</button>
						<button
							type="button"
							on:click={handleCancel}
							class="btn btn-outline w-full"
						>
							取消
						</button>
					</div>
				</div>
			</div>
		</div>
	</form>
</div>
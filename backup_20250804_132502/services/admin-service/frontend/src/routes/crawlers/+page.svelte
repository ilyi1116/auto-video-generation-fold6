<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiClient } from '$utils/api';
	import { authStore } from '$stores/auth';
	import { toast } from 'svelte-french-toast';
	import { 
		Search, 
		Plus, 
		Edit, 
		Trash2, 
		Play, 
		Pause, 
		RotateCcw,
		Clock,
		Globe,
		Settings,
		ChevronDown,
		Calendar,
		FileText
	} from 'lucide-svelte';

	interface CrawlerConfig {
		id: number;
		name: string;
		description: string;
		target_url: string;
		keywords: string[];
		schedule_type: 'once' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'custom_cron';
		status: 'active' | 'inactive' | 'error' | 'paused';
		max_pages: number;
		delay_seconds: number;
		last_run_at: string | null;
		next_run_at: string | null;
		created_at: string;
		updated_at: string | null;
	}

	let configs: CrawlerConfig[] = [];
	let loading = true;
	let searchTerm = '';
	let selectedStatus = '';
	let selectedSchedule = '';
	let currentPage = 1;
	let totalPages = 1;
	let pageSize = 10;
	let total = 0;

	// 狀態選項
	const statusOptions = [
		{ value: '', label: '全部狀態' },
		{ value: 'active', label: '運行中' },
		{ value: 'inactive', label: '已停用' },
		{ value: 'error', label: '錯誤' },
		{ value: 'paused', label: '已暫停' }
	];

	// 排程類型選項
	const scheduleOptions = [
		{ value: '', label: '全部排程' },
		{ value: 'once', label: '單次執行' },
		{ value: 'hourly', label: '每小時' },
		{ value: 'daily', label: '每日' },
		{ value: 'weekly', label: '每週' },
		{ value: 'monthly', label: '每月' },
		{ value: 'custom_cron', label: '自定義' }
	];

	// 狀態樣式
	function getStatusStyle(status: string) {
		switch (status) {
			case 'active':
				return 'bg-green-100 text-green-800 border-green-200';
			case 'inactive':
				return 'bg-gray-100 text-gray-800 border-gray-200';
			case 'error':
				return 'bg-red-100 text-red-800 border-red-200';
			case 'paused':
				return 'bg-yellow-100 text-yellow-800 border-yellow-200';
			default:
				return 'bg-gray-100 text-gray-800 border-gray-200';
		}
	}

	// 狀態文字
	function getStatusText(status: string) {
		switch (status) {
			case 'active':
				return '運行中';
			case 'inactive':
				return '已停用';
			case 'error':
				return '錯誤';
			case 'paused':
				return '已暫停';
			default:
				return '未知';
		}
	}

	// 排程類型文字
	function getScheduleText(type: string) {
		switch (type) {
			case 'once':
				return '單次';
			case 'hourly':
				return '每小時';
			case 'daily':
				return '每日';
			case 'weekly':
				return '每週';
			case 'monthly':
				return '每月';
			case 'custom_cron':
				return '自定義';
			default:
				return '未知';
		}
	}

	// 格式化日期
	function formatDate(dateStr: string | null) {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleString('zh-TW');
	}

	// 載入爬蟲配置
	async function loadConfigs() {
		try {
			loading = true;
			const params = {
				skip: (currentPage - 1) * pageSize,
				limit: pageSize,
				search: searchTerm || undefined,
				status: selectedStatus || undefined,
				schedule_type: selectedSchedule || undefined
			};

			const response = await apiClient.crawlers.list(params);
			if (response.data.success) {
				configs = response.data.data;
				total = response.data.total || configs.length;
				totalPages = Math.ceil(total / pageSize);
			} else {
				toast.error(response.data.message || '載入失敗');
			}
		} catch (error) {
			console.error('載入爬蟲配置失敗:', error);
			toast.error('載入爬蟲配置失敗');
		} finally {
			loading = false;
		}
	}

	// 刪除配置
	async function deleteConfig(config: CrawlerConfig) {
		if (!confirm(`確定要刪除爬蟲配置 "${config.name}" 嗎？`)) {
			return;
		}

		try {
			const response = await apiClient.crawlers.delete(config.id);
			if (response.data.success) {
				toast.success('刪除成功');
				await loadConfigs();
			} else {
				toast.error(response.data.message || '刪除失敗');
			}
		} catch (error) {
			console.error('刪除失敗:', error);
			toast.error('刪除失敗');
		}
	}

	// 運行爬蟲
	async function runCrawler(config: CrawlerConfig) {
		try {
			const response = await apiClient.crawlers.run(config.id);
			if (response.data.success) {
				toast.success('爬蟲已啟動');
				await loadConfigs();
			} else {
				toast.error(response.data.message || '啟動失敗');
			}
		} catch (error) {
			console.error('啟動爬蟲失敗:', error);
			toast.error('啟動爬蟲失敗');
		}
	}

	// 切換狀態
	async function toggleStatus(config: CrawlerConfig) {
		const newStatus = config.status === 'active' ? 'paused' : 'active';
		
		try {
			const response = await apiClient.crawlers.update(config.id, {
				status: newStatus
			});
			if (response.data.success) {
				toast.success('狀態更新成功');
				await loadConfigs();
			} else {
				toast.error(response.data.message || '狀態更新失敗');
			}
		} catch (error) {
			console.error('狀態更新失敗:', error);
			toast.error('狀態更新失敗');
		}
	}

	// 查看結果
	function viewResults(config: CrawlerConfig) {
		goto(`/crawlers/${config.id}/results`);
	}

	// 編輯配置
	function editConfig(config: CrawlerConfig) {
		goto(`/crawlers/${config.id}/edit`);
	}

	// 創建新配置
	function createConfig() {
		goto('/crawlers/create');
	}

	// 搜索處理
	function handleSearch() {
		currentPage = 1;
		loadConfigs();
	}

	// 篩選處理
	function handleFilter() {
		currentPage = 1;
		loadConfigs();
	}

	// 頁面切換
	function goToPage(page: number) {
		currentPage = page;
		loadConfigs();
	}

	// 檢查權限
	$: canManage = $authStore.user?.role === 'super_admin' || 
		$authStore.user?.permissions?.includes('crawler:write');

	onMount(() => {
		loadConfigs();
	});
</script>

<svelte:head>
	<title>爬蟲管理 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">爬蟲管理</h1>
			<p class="mt-2 text-gray-600">管理網站爬蟲配置和監控爬取任務</p>
		</div>
		{#if canManage}
			<button
				on:click={createConfig}
				class="btn btn-primary"
			>
				<Plus class="w-4 h-4 mr-2" />
				新增爬蟲
			</button>
		{/if}
	</div>

	<!-- 篩選和搜索 -->
	<div class="card">
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
			<!-- 搜索 -->
			<div class="relative">
				<Search class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
				<input
					type="text"
					placeholder="搜索爬蟲名稱或URL..."
					bind:value={searchTerm}
					on:input={handleSearch}
					class="form-input pl-10"
				/>
			</div>

			<!-- 狀態篩選 -->
			<div class="relative">
				<select
					bind:value={selectedStatus}
					on:change={handleFilter}
					class="form-select"
				>
					{#each statusOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 排程篩選 -->
			<div class="relative">
				<select
					bind:value={selectedSchedule}
					on:change={handleFilter}
					class="form-select"
				>
					{#each scheduleOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 刷新按鈕 -->
			<button
				on:click={loadConfigs}
				class="btn btn-outline"
				disabled={loading}
			>
				<RotateCcw class="w-4 h-4 mr-2" class:animate-spin={loading} />
				刷新
			</button>
		</div>
	</div>

	<!-- 統計卡片 -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-blue-100 rounded-lg">
					<Settings class="w-6 h-6 text-blue-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">總配置數</p>
					<p class="text-2xl font-bold text-gray-900">{total}</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-green-100 rounded-lg">
					<Play class="w-6 h-6 text-green-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">運行中</p>
					<p class="text-2xl font-bold text-gray-900">
						{configs.filter(c => c.status === 'active').length}
					</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-yellow-100 rounded-lg">
					<Pause class="w-6 h-6 text-yellow-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">已暫停</p>
					<p class="text-2xl font-bold text-gray-900">
						{configs.filter(c => c.status === 'paused').length}
					</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-red-100 rounded-lg">
					<Trash2 class="w-6 h-6 text-red-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">錯誤</p>
					<p class="text-2xl font-bold text-gray-900">
						{configs.filter(c => c.status === 'error').length}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- 爬蟲配置列表 -->
	<div class="card">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				<span class="ml-3 text-gray-600">載入中...</span>
			</div>
		{:else if configs.length === 0}
			<div class="text-center py-12">
				<Settings class="mx-auto h-12 w-12 text-gray-400" />
				<h3 class="mt-2 text-sm font-medium text-gray-900">沒有爬蟲配置</h3>
				<p class="mt-1 text-sm text-gray-500">開始創建您的第一個爬蟲配置。</p>
				{#if canManage}
					<div class="mt-6">
						<button
							on:click={createConfig}
							class="btn btn-primary"
						>
							<Plus class="w-4 h-4 mr-2" />
							新增爬蟲
						</button>
					</div>
				{/if}
			</div>
		{:else}
			<!-- 桌面版表格 -->
			<div class="hidden lg:block overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								爬蟲名稱
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								目標網站
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								關鍵字
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								排程
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								狀態
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								最後執行
							</th>
							<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
								操作
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each configs as config}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4 whitespace-nowrap">
									<div>
										<div class="text-sm font-medium text-gray-900">{config.name}</div>
										{#if config.description}
											<div class="text-sm text-gray-500">{config.description}</div>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Globe class="w-4 h-4 text-gray-400 mr-2" />
										<span class="text-sm text-gray-900 max-w-xs truncate" title={config.target_url}>
											{config.target_url}
										</span>
									</div>
								</td>
								<td class="px-6 py-4">
									<div class="flex flex-wrap gap-1">
										{#each config.keywords.slice(0, 3) as keyword}
											<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
												{keyword}
											</span>
										{/each}
										{#if config.keywords.length > 3}
											<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
												+{config.keywords.length - 3}
											</span>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Clock class="w-4 h-4 text-gray-400 mr-2" />
										<span class="text-sm text-gray-900">{getScheduleText(config.schedule_type)}</span>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(config.status)}">
										{getStatusText(config.status)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDate(config.last_run_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<div class="flex items-center justify-end space-x-2">
										<button
											on:click={() => runCrawler(config)}
											class="text-green-600 hover:text-green-900"
											title="運行爬蟲"
										>
											<Play class="w-4 h-4" />
										</button>
										<button
											on:click={() => viewResults(config)}
											class="text-blue-600 hover:text-blue-900"
											title="查看結果"
										>
											<FileText class="w-4 h-4" />
										</button>
										<button
											on:click={() => toggleStatus(config)}
											class="text-yellow-600 hover:text-yellow-900"
											title={config.status === 'active' ? '暫停' : '啟動'}
										>
											{#if config.status === 'active'}
												<Pause class="w-4 h-4" />
											{:else}
												<Play class="w-4 h-4" />
											{/if}
										</button>
										{#if canManage}
											<button
												on:click={() => editConfig(config)}
												class="text-indigo-600 hover:text-indigo-900"
												title="編輯"
											>
												<Edit class="w-4 h-4" />
											</button>
											<button
												on:click={() => deleteConfig(config)}
												class="text-red-600 hover:text-red-900"
												title="刪除"
											>
												<Trash2 class="w-4 h-4" />
											</button>
										{/if}
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- 移動版卡片 -->
			<div class="lg:hidden space-y-4">
				{#each configs as config}
					<div class="border border-gray-200 rounded-lg p-4">
						<div class="flex items-start justify-between">
							<div class="flex-1 min-w-0">
								<h3 class="text-sm font-medium text-gray-900 truncate">{config.name}</h3>
								{#if config.description}
									<p class="text-sm text-gray-500 mt-1">{config.description}</p>
								{/if}
								<div class="flex items-center mt-2">
									<Globe class="w-4 h-4 text-gray-400 mr-1" />
									<span class="text-xs text-gray-500 truncate">{config.target_url}</span>
								</div>
								<div class="flex items-center mt-1">
									<Clock class="w-4 h-4 text-gray-400 mr-1" />
									<span class="text-xs text-gray-500">{getScheduleText(config.schedule_type)}</span>
									<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(config.status)}">
										{getStatusText(config.status)}
									</span>
								</div>
								<div class="flex flex-wrap gap-1 mt-2">
									{#each config.keywords.slice(0, 2) as keyword}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
											{keyword}
										</span>
									{/each}
									{#if config.keywords.length > 2}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
											+{config.keywords.length - 2}
										</span>
									{/if}
								</div>
							</div>
							<div class="flex flex-col space-y-1 ml-4">
								<button
									on:click={() => runCrawler(config)}
									class="text-green-600 hover:text-green-900"
									title="運行爬蟲"
								>
									<Play class="w-4 h-4" />
								</button>
								<button
									on:click={() => viewResults(config)}
									class="text-blue-600 hover:text-blue-900"
									title="查看結果"
								>
									<FileText class="w-4 h-4" />
								</button>
								{#if canManage}
									<button
										on:click={() => editConfig(config)}
										class="text-indigo-600 hover:text-indigo-900"
										title="編輯"
									>
										<Edit class="w-4 h-4" />
									</button>
									<button
										on:click={() => deleteConfig(config)}
										class="text-red-600 hover:text-red-900"
										title="刪除"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								{/if}
							</div>
						</div>
						{#if config.last_run_at}
							<div class="text-xs text-gray-500 mt-2">
								最後執行: {formatDate(config.last_run_at)}
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<!-- 分頁 -->
			{#if totalPages > 1}
				<div class="flex items-center justify-between mt-6">
					<div class="text-sm text-gray-700">
						顯示第 {(currentPage - 1) * pageSize + 1} 到 {Math.min(currentPage * pageSize, total)} 項，共 {total} 項
					</div>
					<div class="flex space-x-2">
						<button
							on:click={() => goToPage(currentPage - 1)}
							disabled={currentPage === 1}
							class="btn btn-outline btn-sm"
						>
							上一頁
						</button>
						{#each Array.from({length: Math.min(5, totalPages)}, (_, i) => {
							const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
							return start + i;
						}) as page}
							<button
								on:click={() => goToPage(page)}
								class="btn btn-sm {page === currentPage ? 'btn-primary' : 'btn-outline'}"
							>
								{page}
							</button>
						{/each}
						<button
							on:click={() => goToPage(currentPage + 1)}
							disabled={currentPage === totalPages}
							class="btn btn-outline btn-sm"
						>
							下一頁
						</button>
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>
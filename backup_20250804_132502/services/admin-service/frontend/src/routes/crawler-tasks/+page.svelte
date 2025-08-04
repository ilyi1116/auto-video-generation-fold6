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
		Settings,
		ChevronDown,
		Calendar,
		FileText,
		Target,
		Tag
	} from 'lucide-svelte';

	interface CrawlerTask {
		id: number;
		task_name: string;
		keywords: string[];
		target_url: string | null;
		schedule_type: 'daily' | 'weekly' | 'hourly' | 'cron';
		schedule_time: string | null;
		last_run_at: string | null;
		is_active: boolean;
		created_at: string;
		updated_at: string | null;
	}

	let tasks: CrawlerTask[] = [];
	let loading = true;
	let searchTerm = '';
	let selectedSchedule = '';
	let selectedStatus = '';
	let currentPage = 1;
	let totalPages = 1;
	let pageSize = 10;
	let total = 0;

	// 排程類型選項
	const scheduleOptions = [
		{ value: '', label: '全部排程' },
		{ value: 'daily', label: '每日' },
		{ value: 'weekly', label: '每週' },
		{ value: 'hourly', label: '每小時' },
		{ value: 'cron', label: '自定義 Cron' }
	];

	// 狀態選項
	const statusOptions = [
		{ value: '', label: '全部狀態' },
		{ value: 'active', label: '啟用' },
		{ value: 'inactive', label: '停用' }
	];

	// 狀態樣式
	function getStatusStyle(isActive: boolean) {
		return isActive 
			? 'bg-green-100 text-green-800 border-green-200'
			: 'bg-gray-100 text-gray-800 border-gray-200';
	}

	// 狀態文字
	function getStatusText(isActive: boolean) {
		return isActive ? '啟用' : '停用';
	}

	// 排程類型文字
	function getScheduleText(type: string) {
		switch (type) {
			case 'daily':
				return '每日';
			case 'weekly':
				return '每週';
			case 'hourly':
				return '每小時';
			case 'cron':
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

	// 載入爬蟲任務
	async function loadTasks() {
		try {
			loading = true;
			const params = {
				skip: (currentPage - 1) * pageSize,
				limit: pageSize
			};

			const response = await apiClient.crawlerTasks.list(params);
			if (response.data.success) {
				tasks = response.data.data;
				total = response.data.data.length; // 簡化實現
				totalPages = Math.ceil(total / pageSize);
			} else {
				toast.error(response.data.message || '載入失敗');
			}
		} catch (error) {
			console.error('載入爬蟲任務失敗:', error);
			toast.error('載入爬蟲任務失敗');
		} finally {
			loading = false;
		}
	}

	// 刪除任務
	async function deleteTask(task: CrawlerTask) {
		if (!confirm(`確定要刪除爬蟲任務 "${task.task_name}" 嗎？`)) {
			return;
		}

		try {
			const response = await apiClient.crawlerTasks.delete(task.id);
			if (response.data.success) {
				toast.success('刪除成功');
				await loadTasks();
			} else {
				toast.error(response.data.message || '刪除失敗');
			}
		} catch (error) {
			console.error('刪除失敗:', error);
			toast.error('刪除失敗');
		}
	}

	// 運行任務
	async function runTask(task: CrawlerTask) {
		try {
			const response = await apiClient.crawlerTasks.run(task.id);
			if (response.data.success) {
				toast.success('任務已啟動');
				await loadTasks();
			} else {
				toast.error(response.data.message || '啟動失敗');
			}
		} catch (error) {
			console.error('啟動任務失敗:', error);
			toast.error('啟動任務失敗');
		}
	}

	// 切換狀態
	async function toggleStatus(task: CrawlerTask) {
		const newStatus = !task.is_active;
		
		try {
			const response = await apiClient.crawlerTasks.update(task.id, {
				is_active: newStatus
			});
			if (response.data.success) {
				toast.success('狀態更新成功');
				await loadTasks();
			} else {
				toast.error(response.data.message || '狀態更新失敗');
			}
		} catch (error) {
			console.error('狀態更新失敗:', error);
			toast.error('狀態更新失敗');
		}
	}

	// 編輯任務
	function editTask(task: CrawlerTask) {
		goto(`/crawler-tasks/${task.id}/edit`);
	}

	// 創建新任務
	function createTask() {
		goto('/crawler-tasks/create');
	}

	// 搜索處理
	function handleSearch() {
		currentPage = 1;
		// 這裡可以添加實際的搜索邏輯
		loadTasks();
	}

	// 篩選處理
	function handleFilter() {
		currentPage = 1;
		// 這裡可以添加實際的篩選邏輯
		loadTasks();
	}

	// 頁面切換
	function goToPage(page: number) {
		currentPage = page;
		loadTasks();
	}

	// 檢查權限
	$: canManage = $authStore.user?.role === 'super_admin' || 
		$authStore.user?.permissions?.includes('crawler:write');

	onMount(() => {
		loadTasks();
	});
</script>

<svelte:head>
	<title>爬蟲任務管理 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">爬蟲任務管理</h1>
			<p class="mt-2 text-gray-600">管理爬蟲任務的關鍵字、目標網址與排程設定</p>
		</div>
		{#if canManage}
			<button
				on:click={createTask}
				class="btn btn-primary"
			>
				<Plus class="w-4 h-4 mr-2" />
				新增任務
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
					placeholder="搜索任務名稱..."
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
				on:click={loadTasks}
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
					<p class="text-sm font-medium text-gray-600">總任務數</p>
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
					<p class="text-sm font-medium text-gray-600">啟用中</p>
					<p class="text-2xl font-bold text-gray-900">
						{tasks.filter(t => t.is_active).length}
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
					<p class="text-sm font-medium text-gray-600">已停用</p>
					<p class="text-2xl font-bold text-gray-900">
						{tasks.filter(t => !t.is_active).length}
					</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-purple-100 rounded-lg">
					<Calendar class="w-6 h-6 text-purple-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">今日執行</p>
					<p class="text-2xl font-bold text-gray-900">
						{tasks.filter(t => {
							if (!t.last_run_at) return false;
							const lastRun = new Date(t.last_run_at);
							const today = new Date();
							return lastRun.toDateString() === today.toDateString();
						}).length}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- 爬蟲任務列表 -->
	<div class="card">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				<span class="ml-3 text-gray-600">載入中...</span>
			</div>
		{:else if tasks.length === 0}
			<div class="text-center py-12">
				<Settings class="mx-auto h-12 w-12 text-gray-400" />
				<h3 class="mt-2 text-sm font-medium text-gray-900">沒有爬蟲任務</h3>
				<p class="mt-1 text-sm text-gray-500">開始創建您的第一個爬蟲任務。</p>
				{#if canManage}
					<div class="mt-6">
						<button
							on:click={createTask}
							class="btn btn-primary"
						>
							<Plus class="w-4 h-4 mr-2" />
							新增任務
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
								任務名稱
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								關鍵字
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								目標網址
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
						{#each tasks as task}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm font-medium text-gray-900">{task.task_name}</div>
								</td>
								<td class="px-6 py-4">
									<div class="flex flex-wrap gap-1">
										{#each task.keywords.slice(0, 3) as keyword}
											<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
												{keyword}
											</span>
										{/each}
										{#if task.keywords.length > 3}
											<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
												+{task.keywords.length - 3}
											</span>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									{#if task.target_url}
										<div class="flex items-center">
											<Target class="w-4 h-4 text-gray-400 mr-2" />
											<span class="text-sm text-gray-900 max-w-xs truncate" title={task.target_url}>
												{task.target_url}
											</span>
										</div>
									{:else}
										<span class="text-sm text-gray-500">-</span>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Clock class="w-4 h-4 text-gray-400 mr-2" />
										<div>
											<div class="text-sm text-gray-900">{getScheduleText(task.schedule_type)}</div>
											{#if task.schedule_time}
												<div class="text-xs text-gray-500">{task.schedule_time}</div>
											{/if}
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(task.is_active)}">
										{getStatusText(task.is_active)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDate(task.last_run_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<div class="flex items-center justify-end space-x-2">
										<button
											on:click={() => runTask(task)}
											class="text-green-600 hover:text-green-900"
											title="運行任務"
											disabled={!task.is_active}
										>
											<Play class="w-4 h-4" />
										</button>
										<button
											on:click={() => toggleStatus(task)}
											class="text-yellow-600 hover:text-yellow-900"
											title={task.is_active ? '停用' : '啟用'}
										>
											{#if task.is_active}
												<Pause class="w-4 h-4" />
											{:else}
												<Play class="w-4 h-4" />
											{/if}
										</button>
										{#if canManage}
											<button
												on:click={() => editTask(task)}
												class="text-indigo-600 hover:text-indigo-900"
												title="編輯"
											>
												<Edit class="w-4 h-4" />
											</button>
											<button
												on:click={() => deleteTask(task)}
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
				{#each tasks as task}
					<div class="border border-gray-200 rounded-lg p-4">
						<div class="flex items-start justify-between">
							<div class="flex-1 min-w-0">
								<h3 class="text-sm font-medium text-gray-900 truncate">{task.task_name}</h3>
								{#if task.target_url}
									<div class="flex items-center mt-2">
										<Target class="w-4 h-4 text-gray-400 mr-1" />
										<span class="text-xs text-gray-500 truncate">{task.target_url}</span>
									</div>
								{/if}
								<div class="flex items-center mt-1">
									<Clock class="w-4 h-4 text-gray-400 mr-1" />
									<span class="text-xs text-gray-500">{getScheduleText(task.schedule_type)}</span>
									{#if task.schedule_time}
										<span class="text-xs text-gray-400 ml-1">({task.schedule_time})</span>
									{/if}
									<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(task.is_active)}">
										{getStatusText(task.is_active)}
									</span>
								</div>
								<div class="flex flex-wrap gap-1 mt-2">
									{#each task.keywords.slice(0, 2) as keyword}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
											{keyword}
										</span>
									{/each}
									{#if task.keywords.length > 2}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
											+{task.keywords.length - 2}
										</span>
									{/if}
								</div>
							</div>
							<div class="flex flex-col space-y-1 ml-4">
								<button
									on:click={() => runTask(task)}
									class="text-green-600 hover:text-green-900"
									title="運行任務"
									disabled={!task.is_active}
								>
									<Play class="w-4 h-4" />
								</button>
								<button
									on:click={() => toggleStatus(task)}
									class="text-yellow-600 hover:text-yellow-900"
									title={task.is_active ? '停用' : '啟用'}
								>
									{#if task.is_active}
										<Pause class="w-4 h-4" />
									{:else}
										<Play class="w-4 h-4" />
									{/if}
								</button>
								{#if canManage}
									<button
										on:click={() => editTask(task)}
										class="text-indigo-600 hover:text-indigo-900"
										title="編輯"
									>
										<Edit class="w-4 h-4" />
									</button>
									<button
										on:click={() => deleteTask(task)}
										class="text-red-600 hover:text-red-900"
										title="刪除"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								{/if}
							</div>
						</div>
						{#if task.last_run_at}
							<div class="text-xs text-gray-500 mt-2">
								最後執行: {formatDate(task.last_run_at)}
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
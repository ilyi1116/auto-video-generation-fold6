<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiClient } from '$utils/api';
	import { toast } from 'svelte-french-toast';
	import { 
		ArrowLeft, 
		Download, 
		Search, 
		Calendar, 
		FileText, 
		Globe, 
		Clock,
		ChevronDown,
		ExternalLink,
		RotateCcw,
		Filter
	} from 'lucide-svelte';

	interface CrawlerResult {
		id: number;
		run_id: string;
		url: string;
		title: string;
		content: string;
		metadata: Record<string, any>;
		extracted_data: Record<string, any>;
		status: 'success' | 'failed' | 'partial';
		error_message: string | null;
		crawled_at: string;
		processing_time: number;
	}

	interface CrawlerConfig {
		id: number;
		name: string;
		description: string;
		target_url: string;
		keywords: string[];
	}

	let configId = parseInt($page.params.id);
	let config: CrawlerConfig | null = null;
	let results: CrawlerResult[] = [];
	let loading = true;
	let loadingResults = false;
	
	// 篩選和搜索
	let searchTerm = '';
	let statusFilter = '';
	let dateFrom = '';
	let dateTo = '';
	let currentPage = 1;
	let pageSize = 10;
	let total = 0;
	let totalPages = 1;

	// 狀態選項
	const statusOptions = [
		{ value: '', label: '全部狀態' },
		{ value: 'success', label: '成功' },
		{ value: 'failed', label: '失敗' },
		{ value: 'partial', label: '部分成功' }
	];

	// 獲取配置信息
	async function loadConfig() {
		try {
			const response = await apiClient.crawlers.get(configId);
			if (response.data.success) {
				config = response.data.data;
			} else {
				toast.error('載入配置失敗');
				goto('/crawlers');
			}
		} catch (error) {
			console.error('載入配置失敗:', error);
			toast.error('載入配置失敗');
			goto('/crawlers');
		}
	}

	// 載入爬蟲結果
	async function loadResults() {
		try {
			loadingResults = true;
			const params = {
				skip: (currentPage - 1) * pageSize,
				limit: pageSize,
				search: searchTerm || undefined,
				status: statusFilter || undefined,
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined
			};

			const response = await apiClient.crawlers.getResults(configId, params);
			if (response.data.success) {
				results = response.data.data;
				total = response.data.total || results.length;
				totalPages = Math.ceil(total / pageSize);
			} else {
				toast.error(response.data.message || '載入結果失敗');
			}
		} catch (error) {
			console.error('載入結果失敗:', error);
			toast.error('載入結果失敗');
		} finally {
			loadingResults = false;
		}
	}

	// 導出結果
	async function exportResults() {
		try {
			const params = {
				search: searchTerm || undefined,
				status: statusFilter || undefined,
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined,
				format: 'csv'
			};

			const response = await apiClient.crawlers.exportResults(configId, params);
			
			// 創建下載連結
			const blob = new Blob([response.data], { type: 'text/csv' });
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `crawler_results_${configId}_${new Date().toISOString().split('T')[0]}.csv`;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
			
			toast.success('結果已導出');
		} catch (error) {
			console.error('導出失敗:', error);
			toast.error('導出失敗');
		}
	}

	// 格式化狀態
	function getStatusStyle(status: string) {
		switch (status) {
			case 'success':
				return 'bg-green-100 text-green-800 border-green-200';
			case 'failed':
				return 'bg-red-100 text-red-800 border-red-200';
			case 'partial':
				return 'bg-yellow-100 text-yellow-800 border-yellow-200';
			default:
				return 'bg-gray-100 text-gray-800 border-gray-200';
		}
	}

	function getStatusText(status: string) {
		switch (status) {
			case 'success':
				return '成功';
			case 'failed':
				return '失敗';
			case 'partial':
				return '部分成功';
			default:
				return '未知';
		}
	}

	// 格式化日期
	function formatDate(dateStr: string) {
		return new Date(dateStr).toLocaleString('zh-TW');
	}

	// 格式化處理時間
	function formatProcessingTime(time: number) {
		return time < 1000 ? `${time}ms` : `${(time / 1000).toFixed(2)}s`;
	}

	// 截斷文字
	function truncateText(text: string, maxLength: number = 100) {
		return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
	}

	// 搜索處理
	function handleSearch() {
		currentPage = 1;
		loadResults();
	}

	// 篩選處理
	function handleFilter() {
		currentPage = 1;
		loadResults();
	}

	// 頁面切換
	function goToPage(page: number) {
		currentPage = page;
		loadResults();
	}

	// 查看結果詳情
	function viewResultDetail(result: CrawlerResult) {
		// 在新視窗中顯示結果詳情
		const detailWindow = window.open('', '_blank', 'width=800,height=600');
		if (detailWindow) {
			detailWindow.document.write(`
				<html>
					<head>
						<title>爬蟲結果詳情 - ${result.run_id}</title>
						<style>
							body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
							.header { border-bottom: 1px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 20px; }
							.section { margin-bottom: 20px; }
							.label { font-weight: 600; color: #374151; }
							.content { background: #f9fafb; padding: 12px; border-radius: 6px; margin-top: 8px; white-space: pre-wrap; }
							.metadata { background: #f3f4f6; padding: 12px; border-radius: 6px; }
						</style>
					</head>
					<body>
						<div class="header">
							<h1>爬蟲結果詳情</h1>
							<p><strong>運行 ID:</strong> ${result.run_id}</p>
							<p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
							<p><strong>爬取時間:</strong> ${formatDate(result.crawled_at)}</p>
							<p><strong>處理時間:</strong> ${formatProcessingTime(result.processing_time)}</p>
							<p><strong>狀態:</strong> ${getStatusText(result.status)}</p>
						</div>
						
						<div class="section">
							<div class="label">標題:</div>
							<div class="content">${result.title || '無標題'}</div>
						</div>
						
						<div class="section">
							<div class="label">內容:</div>
							<div class="content">${result.content || '無內容'}</div>
						</div>
						
						${result.extracted_data && Object.keys(result.extracted_data).length > 0 ? `
						<div class="section">
							<div class="label">提取的數據:</div>
							<div class="metadata">${JSON.stringify(result.extracted_data, null, 2)}</div>
						</div>
						` : ''}
						
						${result.metadata && Object.keys(result.metadata).length > 0 ? `
						<div class="section">
							<div class="label">元數據:</div>
							<div class="metadata">${JSON.stringify(result.metadata, null, 2)}</div>
						</div>
						` : ''}
						
						${result.error_message ? `
						<div class="section">
							<div class="label">錯誤信息:</div>
							<div class="content" style="background: #fef2f2; color: #991b1b;">${result.error_message}</div>
						</div>
						` : ''}
					</body>
				</html>
			`);
		}
	}

	// 返回爬蟲列表
	function goBack() {
		goto('/crawlers');
	}

	onMount(async () => {
		loading = true;
		await Promise.all([loadConfig(), loadResults()]);
		loading = false;
	});
</script>

<svelte:head>
	<title>爬蟲結果 - {config?.name || '載入中'} - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center">
		<button
			on:click={goBack}
			class="mr-4 p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
		>
			<ArrowLeft class="w-5 h-5" />
		</button>
		<div class="flex-1">
			{#if config}
				<h1 class="text-2xl font-bold text-gray-900">{config.name} - 爬蟲結果</h1>
				<p class="mt-2 text-gray-600">
					目標網站: <a href={config.target_url} target="_blank" class="text-blue-600 hover:text-blue-800">
						{config.target_url}
						<ExternalLink class="w-4 h-4 inline ml-1" />
					</a>
				</p>
				{#if config.description}
					<p class="text-gray-600">{config.description}</p>
				{/if}
			{:else}
				<h1 class="text-2xl font-bold text-gray-900">載入中...</h1>
			{/if}
		</div>
		<button
			on:click={exportResults}
			class="btn btn-outline"
		>
			<Download class="w-4 h-4 mr-2" />
			導出結果
		</button>
	</div>

	<!-- 篩選和搜索 -->
	<div class="card">
		<div class="grid grid-cols-1 md:grid-cols-5 gap-4">
			<!-- 搜索 -->
			<div class="relative">
				<Search class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
				<input
					type="text"
					placeholder="搜索標題或內容..."
					bind:value={searchTerm}
					on:input={handleSearch}
					class="form-input pl-10"
				/>
			</div>

			<!-- 狀態篩選 -->
			<div class="relative">
				<select
					bind:value={statusFilter}
					on:change={handleFilter}
					class="form-select"
				>
					{#each statusOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 開始日期 -->
			<div class="relative">
				<Calendar class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
				<input
					type="date"
					bind:value={dateFrom}
					on:change={handleFilter}
					class="form-input pl-10"
					placeholder="開始日期"
				/>
			</div>

			<!-- 結束日期 -->
			<div class="relative">
				<Calendar class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
				<input
					type="date"
					bind:value={dateTo}
					on:change={handleFilter}
					class="form-input pl-10"
					placeholder="結束日期"
				/>
			</div>

			<!-- 刷新按鈕 -->
			<button
				on:click={loadResults}
				class="btn btn-outline"
				disabled={loadingResults}
			>
				<RotateCcw class="w-4 h-4 mr-2" class:animate-spin={loadingResults} />
				刷新
			</button>
		</div>
	</div>

	<!-- 統計卡片 -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-blue-100 rounded-lg">
					<FileText class="w-6 h-6 text-blue-600" />
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">總結果數</p>
					<p class="text-2xl font-bold text-gray-900">{total}</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-green-100 rounded-lg">
					<div class="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center">
						<span class="text-white text-xs">✓</span>
					</div>
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">成功</p>
					<p class="text-2xl font-bold text-gray-900">
						{results.filter(r => r.status === 'success').length}
					</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-yellow-100 rounded-lg">
					<div class="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center">
						<span class="text-white text-xs">!</span>
					</div>
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">部分成功</p>
					<p class="text-2xl font-bold text-gray-900">
						{results.filter(r => r.status === 'partial').length}
					</p>
				</div>
			</div>
		</div>

		<div class="card">
			<div class="flex items-center">
				<div class="p-2 bg-red-100 rounded-lg">
					<div class="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center">
						<span class="text-white text-xs">✗</span>
					</div>
				</div>
				<div class="ml-4">
					<p class="text-sm font-medium text-gray-600">失敗</p>
					<p class="text-2xl font-bold text-gray-900">
						{results.filter(r => r.status === 'failed').length}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- 結果列表 -->
	<div class="card">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				<span class="ml-3 text-gray-600">載入中...</span>
			</div>
		{:else if results.length === 0}
			<div class="text-center py-12">
				<FileText class="mx-auto h-12 w-12 text-gray-400" />
				<h3 class="mt-2 text-sm font-medium text-gray-900">沒有爬蟲結果</h3>
				<p class="mt-1 text-sm text-gray-500">尚未有任何爬取結果。</p>
			</div>
		{:else}
			<!-- 桌面版表格 -->
			<div class="hidden lg:block overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								URL / 標題
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								內容預覽
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								狀態
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								爬取時間
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								處理時間
							</th>
							<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
								操作
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each results as result}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4">
									<div class="max-w-xs">
										<div class="flex items-center">
											<Globe class="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
											<a 
												href={result.url} 
												target="_blank" 
												class="text-sm text-blue-600 hover:text-blue-800 truncate"
												title={result.url}
											>
												{new URL(result.url).hostname}
											</a>
										</div>
										{#if result.title}
											<div class="text-sm font-medium text-gray-900 mt-1 truncate" title={result.title}>
												{result.title}
											</div>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4">
									<div class="text-sm text-gray-900 max-w-xs">
										{truncateText(result.content || '無內容', 80)}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(result.status)}">
										{getStatusText(result.status)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									<div class="flex items-center">
										<Clock class="w-4 h-4 text-gray-400 mr-2" />
										{formatDate(result.crawled_at)}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatProcessingTime(result.processing_time)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<button
										on:click={() => viewResultDetail(result)}
										class="text-blue-600 hover:text-blue-900"
										title="查看詳情"
									>
										<FileText class="w-4 h-4" />
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- 移動版卡片 -->
			<div class="lg:hidden space-y-4">
				{#each results as result}
					<div class="border border-gray-200 rounded-lg p-4">
						<div class="flex items-start justify-between">
							<div class="flex-1 min-w-0">
								<div class="flex items-center">
									<Globe class="w-4 h-4 text-gray-400 mr-2 flex-shrink-0" />
									<a 
										href={result.url} 
										target="_blank" 
										class="text-sm text-blue-600 hover:text-blue-800 truncate"
									>
										{new URL(result.url).hostname}
									</a>
								</div>
								{#if result.title}
									<h3 class="text-sm font-medium text-gray-900 mt-1 truncate">{result.title}</h3>
								{/if}
								<p class="text-sm text-gray-500 mt-1">{truncateText(result.content || '無內容', 60)}</p>
								<div class="flex items-center justify-between mt-2">
									<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {getStatusStyle(result.status)}">
										{getStatusText(result.status)}
									</span>
									<div class="flex items-center text-xs text-gray-500">
										<Clock class="w-3 h-3 mr-1" />
										{formatDate(result.crawled_at)}
									</div>
								</div>
							</div>
							<button
								on:click={() => viewResultDetail(result)}
								class="ml-4 text-blue-600 hover:text-blue-900"
								title="查看詳情"
							>
								<FileText class="w-4 h-4" />
							</button>
						</div>
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
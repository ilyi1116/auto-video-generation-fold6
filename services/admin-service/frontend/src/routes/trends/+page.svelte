<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { apiClient } from '$utils/api';
	import { toast } from 'svelte-french-toast';
	import { 
		TrendingUp, 
		Search, 
		Calendar, 
		Globe,
		Hash,
		BarChart3,
		Download,
		RefreshCw,
		Filter,
		ChevronDown,
		Eye,
		Clock
	} from 'lucide-svelte';

	interface KeywordTrend {
		id: number;
		platform: string;
		keyword: string;
		period: string;
		rank: number;
		search_volume: number | null;
		change_percentage: string | null;
		region: string;
		category: string | null;
		collected_at: string;
		metadata: Record<string, any>;
	}

	interface TrendStats {
		total_keywords: number;
		platforms_count: number;
		top_categories: Array<{ category: string; count: number }>;
		growth_rate: number;
	}

	let keywords: KeywordTrend[] = [];
	let topKeywords: any = {};
	let stats: any = null;
	let loading = true;
	let refreshing = false;

	// 篩選和搜索
	let searchTerm = '';
	let selectedPlatform = '';
	let selectedPeriod = 'day';
	let selectedRegion = '';
	let selectedCategory = '';
	let currentPage = 1;
	let pageSize = 50;
	let total = 0;
	let totalPages = 1;

	// 自動刷新
	let autoRefresh = false;
	let refreshInterval: number | null = null;

	// 平台選項
	const platformOptions = [
		{ value: '', label: '全部平台', color: 'gray' },
		{ value: 'TikTok', label: 'TikTok', color: 'black' },
		{ value: 'YouTube', label: 'YouTube', color: 'red' },
		{ value: 'Instagram', label: 'Instagram', color: 'pink' },
		{ value: 'Facebook', label: 'Facebook', color: 'blue' },
		{ value: 'Twitter', label: 'Twitter', color: 'sky' }
	];

	// 時間週期選項
	const periodOptions = [
		{ value: 'day', label: '每日' },
		{ value: 'week', label: '每週' },
		{ value: 'month', label: '每月' },
		{ value: '3_months', label: '3個月' },
		{ value: '6_months', label: '6個月' }
	];

	// 地區選項
	const regionOptions = [
		{ value: '', label: '全部地區' },
		{ value: 'global', label: '全球' },
		{ value: 'US', label: '美國' },
		{ value: 'TW', label: '台灣' },
		{ value: 'JP', label: '日本' },
		{ value: 'KR', label: '韓國' },
		{ value: 'CN', label: '中國' }
	];

	// 平台顏色
	function getPlatformColor(platform: string) {
		const platformConfig = platformOptions.find(p => p.value === platform);
		return platformConfig?.color || 'gray';
	}

	// 平台圖標
	function getPlatformIcon(platform: string) {
		switch (platform.toLowerCase()) {
			case 'tiktok':
				return '🎵';
			case 'youtube':
				return '📺';
			case 'instagram':
				return '📷';
			case 'facebook':
				return '👥';
			case 'twitter':
				return '🐦';
			default:
				return '🌐';
		}
	}

	// 時間週期標籤
	function getPeriodLabel(period: string) {
		const option = periodOptions.find(p => p.value === period);
		return option?.label || period;
	}

	// 格式化分數
	function formatScore(score: number) {
		if (score >= 1000000) {
			return `${(score / 1000000).toFixed(1)}M`;
		} else if (score >= 1000) {
			return `${(score / 1000).toFixed(1)}K`;
		}
		return score.toString();
	}

	// 格式化日期
	function formatDate(dateStr: string) {
		return new Date(dateStr).toLocaleString('zh-TW');
	}

	// 載入趨勢關鍵字
	async function loadKeywords() {
		try {
			refreshing = true;
			const params = {
				platform: selectedPlatform || undefined,
				period: selectedPeriod,
				limit: pageSize
			};

			const response = await apiClient.keywordTrends.list(params);
			if (response.data.success) {
				keywords = response.data.data.trends || [];
				total = response.data.data.total || keywords.length;
				totalPages = Math.ceil(total / pageSize);
			} else {
				toast.error(response.data.message || '載入失敗');
			}
		} catch (error) {
			console.error('載入趨勢關鍵字失敗:', error);
			toast.error('載入趨勢關鍵字失敗');
		} finally {
			refreshing = false;
		}
	}

	// 載入熱門關鍵字
	async function loadTopKeywords() {
		try {
			const params = {
				period: selectedPeriod,
				top_n: 10
			};

			const response = await apiClient.keywordTrends.platforms(params);
			if (response.data.success) {
				topKeywords = response.data.data.platforms || {};
			}
		} catch (error) {
			console.error('載入熱門關鍵字失敗:', error);
		}
	}

	// 載入統計數據
	async function loadStats() {
		try {
			const params = {
				days: 7
			};

			const response = await apiClient.keywordTrends.statistics(params);
			if (response.data.success) {
				stats = response.data.data;
			}
		} catch (error) {
			console.error('載入統計數據失敗:', error);
		}
	}

	// 搜索處理
	function handleSearch() {
		currentPage = 1;
		loadKeywords();
	}

	// 篩選處理
	function handleFilter() {
		currentPage = 1;
		Promise.all([loadKeywords(), loadTopKeywords(), loadStats()]);
	}

	// 頁面切換
	function goToPage(page: number) {
		currentPage = page;
		loadKeywords();
	}

	// 刷新數據
	async function refreshData() {
		await Promise.all([loadKeywords(), loadTopKeywords(), loadStats()]);
		toast.success('數據已刷新');
	}

	// 導出數據
	async function exportData() {
		try {
			const params = {
				search: searchTerm || undefined,
				platform: selectedPlatform || undefined,
				timeframe: selectedTimeframe || undefined,
				region: selectedRegion || undefined,
				category: selectedCategory || undefined,
				format: 'csv'
			};

			// 這裡應該調用導出 API
			toast.success('導出功能開發中');
		} catch (error) {
			console.error('導出失敗:', error);
			toast.error('導出失敗');
		}
	}

	// 切換自動刷新
	function toggleAutoRefresh() {
		autoRefresh = !autoRefresh;
		if (autoRefresh) {
			refreshInterval = setInterval(() => {
				refreshData();
			}, 60000); // 每分鐘刷新
			toast.success('已啟用自動刷新');
		} else {
			if (refreshInterval) {
				clearInterval(refreshInterval);
				refreshInterval = null;
			}
			toast.success('已停用自動刷新');
		}
	}

	// 查看關鍵字詳情
	function viewKeywordDetail(keyword: TrendingKeyword) {
		// 在新視窗中顯示關鍵字詳情
		const detailWindow = window.open('', '_blank', 'width=600,height=500');
		if (detailWindow) {
			detailWindow.document.write(`
				<html>
					<head>
						<title>關鍵字詳情 - ${keyword.keyword}</title>
						<style>
							body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
							.header { border-bottom: 1px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 20px; }
							.info-item { margin-bottom: 12px; }
							.label { font-weight: 600; color: #374151; }
							.value { margin-left: 8px; color: #111827; }
							.platform { display: inline-block; padding: 4px 8px; border-radius: 6px; color: white; }
							.metadata { background: #f3f4f6; padding: 12px; border-radius: 6px; margin-top: 16px; }
						</style>
					</head>
					<body>
						<div class="header">
							<h1>關鍵字詳情</h1>
							<h2>${keyword.keyword}</h2>
						</div>
						
						<div class="info-item">
							<span class="label">平台:</span>
							<span class="platform" style="background-color: var(--platform-color);">${getPlatformIcon(keyword.platform)} ${keyword.platform.toUpperCase()}</span>
						</div>
						
						<div class="info-item">
							<span class="label">排名:</span>
							<span class="value">#${keyword.rank}</span>
						</div>
						
						<div class="info-item">
							<span class="label">分數:</span>
							<span class="value">${formatScore(keyword.score)}</span>
						</div>
						
						<div class="info-item">
							<span class="label">時間範圍:</span>
							<span class="value">${getTimeframeLabel(keyword.timeframe)}</span>
						</div>
						
						<div class="info-item">
							<span class="label">地區:</span>
							<span class="value">${keyword.region}</span>
						</div>
						
						${keyword.category ? `
						<div class="info-item">
							<span class="label">分類:</span>
							<span class="value">${keyword.category}</span>
						</div>
						` : ''}
						
						<div class="info-item">
							<span class="label">趨勢日期:</span>
							<span class="value">${formatDate(keyword.trend_date)}</span>
						</div>
						
						${keyword.metadata && Object.keys(keyword.metadata).length > 0 ? `
						<div class="metadata">
							<h3>元數據</h3>
							<pre>${JSON.stringify(keyword.metadata, null, 2)}</pre>
						</div>
						` : ''}
					</body>
				</html>
			`);
		}
	}

	onMount(async () => {
		loading = true;
		await Promise.all([loadKeywords(), loadTopKeywords(), loadStats()]);
		loading = false;
	});

	onDestroy(() => {
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
	});
</script>

<svelte:head>
	<title>社交媒體趨勢 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">社交媒體趨勢</h1>
			<p class="mt-2 text-gray-600">追蹤各大社交平台的熱門關鍵字和趨勢分析</p>
		</div>
		<div class="flex space-x-3">
			<button
				on:click={toggleAutoRefresh}
				class="btn {autoRefresh ? 'btn-primary' : 'btn-outline'}"
			>
				<Clock class="w-4 h-4 mr-2" />
				{autoRefresh ? '停用' : '啟用'}自動刷新
			</button>
			<button
				on:click={refreshData}
				disabled={refreshing}
				class="btn btn-outline"
			>
				<RefreshCw class="w-4 h-4 mr-2" class:animate-spin={refreshing} />
				刷新
			</button>
			<button
				on:click={exportData}
				class="btn btn-outline"
			>
				<Download class="w-4 h-4 mr-2" />
				導出
			</button>
		</div>
	</div>

	<!-- 統計卡片 -->
	{#if stats}
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
			<div class="card">
				<div class="flex items-center">
					<div class="p-2 bg-blue-100 rounded-lg">
						<Hash class="w-6 h-6 text-blue-600" />
					</div>
					<div class="ml-4">
						<p class="text-sm font-medium text-gray-600">總關鍵字數</p>
						<p class="text-2xl font-bold text-gray-900">
							{stats.statistics?.reduce((sum, stat) => sum + stat.total_keywords, 0) || 0}
						</p>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="flex items-center">
					<div class="p-2 bg-green-100 rounded-lg">
						<Globe class="w-6 h-6 text-green-600" />
					</div>
					<div class="ml-4">
						<p class="text-sm font-medium text-gray-600">覆蓋平台</p>
						<p class="text-2xl font-bold text-gray-900">{stats.statistics?.length || 0}</p>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="flex items-center">
					<div class="p-2 bg-purple-100 rounded-lg">
						<BarChart3 class="w-6 h-6 text-purple-600" />
					</div>
					<div class="ml-4">
						<p class="text-sm font-medium text-gray-600">獨特關鍵字</p>
						<p class="text-2xl font-bold text-gray-900">
							{stats.statistics?.reduce((sum, stat) => sum + stat.unique_keywords, 0) || 0}
						</p>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="flex items-center">
					<div class="p-2 bg-orange-100 rounded-lg">
						<TrendingUp class="w-6 h-6 text-orange-600" />
					</div>
					<div class="ml-4">
						<p class="text-sm font-medium text-gray-600">統計期間</p>
						<p class="text-2xl font-bold text-gray-900">{stats.period_days || 7} 天</p>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- 熱門關鍵字 -->
	{#if Object.keys(topKeywords).length > 0}
		<div class="card">
			<h2 class="text-lg font-medium text-gray-900 mb-4">🔥 {getPeriodLabel(selectedPeriod)}熱門關鍵字</h2>
			<div class="space-y-6">
				{#each Object.entries(topKeywords) as [platform, keywords]}
					<div>
						<h3 class="text-md font-medium text-gray-800 mb-3 flex items-center">
							<span class="mr-2">{getPlatformIcon(platform)}</span>
							{platform}
						</h3>
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
							{#each keywords.slice(0, 5) as keyword, index}
								<div class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
									 on:click={() => viewKeywordDetail(keyword)}
									 role="button"
									 tabindex="0">
									<div class="flex-shrink-0">
										<span class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium
											{index < 3 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}">
											{keyword.rank}
										</span>
									</div>
									<div class="ml-2 flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900 truncate">{keyword.keyword}</p>
										<div class="flex items-center mt-1">
											<span class="text-xs text-gray-500">{formatScore(keyword.search_volume || 0)}</span>
											{#if keyword.change_percentage}
												<span class="text-xs text-green-600 ml-1">{keyword.change_percentage}</span>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- 篩選和搜索 -->
	<div class="card">
		<div class="grid grid-cols-1 md:grid-cols-6 gap-4">
			<!-- 搜索 -->
			<div class="relative">
				<Search class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
				<input
					type="text"
					placeholder="搜索關鍵字..."
					bind:value={searchTerm}
					on:input={handleSearch}
					class="form-input pl-10"
				/>
			</div>

			<!-- 平台篩選 -->
			<div class="relative">
				<select
					bind:value={selectedPlatform}
					on:change={handleFilter}
					class="form-select"
				>
					{#each platformOptions as platform}
						<option value={platform.value}>{platform.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 時間週期篩選 -->
			<div class="relative">
				<select
					bind:value={selectedPeriod}
					on:change={handleFilter}
					class="form-select"
				>
					{#each periodOptions as period}
						<option value={period.value}>{period.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 地區篩選 -->
			<div class="relative">
				<select
					bind:value={selectedRegion}
					on:change={handleFilter}
					class="form-select"
				>
					{#each regionOptions as region}
						<option value={region.value}>{region.label}</option>
					{/each}
				</select>
				<ChevronDown class="absolute right-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" />
			</div>

			<!-- 分類篩選 -->
			<div class="relative">
				<input
					type="text"
					placeholder="分類篩選..."
					bind:value={selectedCategory}
					on:input={handleFilter}
					class="form-input"
				/>
			</div>

			<!-- 篩選按鈕 -->
			<button
				on:click={handleFilter}
				class="btn btn-outline"
			>
				<Filter class="w-4 h-4 mr-2" />
				篩選
			</button>
		</div>
	</div>

	<!-- 趨勢關鍵字列表 -->
	<div class="card">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				<span class="ml-3 text-gray-600">載入中...</span>
			</div>
		{:else if keywords.length === 0}
			<div class="text-center py-12">
				<TrendingUp class="mx-auto h-12 w-12 text-gray-400" />
				<h3 class="mt-2 text-sm font-medium text-gray-900">沒有趨勢數據</h3>
				<p class="mt-1 text-sm text-gray-500">尚未收集到趨勢關鍵字數據。</p>
			</div>
		{:else}
			<!-- 桌面版表格 -->
			<div class="hidden lg:block overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								排名
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								關鍵字
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								平台
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								分數
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								搜尋量
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								變化
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								收集時間
							</th>
							<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
								操作
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each keywords as keyword}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<span class="inline-flex items-center justify-center w-8 h-8 rounded-full 
											{keyword.rank <= 3 ? 'bg-yellow-100 text-yellow-800' : 
											 keyword.rank <= 10 ? 'bg-blue-100 text-blue-800' : 
											 'bg-gray-100 text-gray-800'}">
											{keyword.rank}
										</span>
									</div>
								</td>
								<td class="px-6 py-4">
									<div class="flex items-center">
										<Hash class="w-4 h-4 text-gray-400 mr-2" />
										<span class="text-sm font-medium text-gray-900">{keyword.keyword}</span>
									</div>
									{#if keyword.category}
										<div class="text-sm text-gray-500">{keyword.category}</div>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
										bg-{getPlatformColor(keyword.platform)}-100 text-{getPlatformColor(keyword.platform)}-800">
										{getPlatformIcon(keyword.platform)} {keyword.platform.toUpperCase()}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{keyword.search_volume ? formatScore(keyword.search_volume) : 'N/A'}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{#if keyword.change_percentage}
										<span class="text-green-600">{keyword.change_percentage}</span>
									{:else}
										N/A
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDate(keyword.collected_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<button
										on:click={() => viewKeywordDetail(keyword)}
										class="text-blue-600 hover:text-blue-900"
										title="查看詳情"
									>
										<Eye class="w-4 h-4" />
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- 移動版卡片 -->
			<div class="lg:hidden space-y-4">
				{#each keywords as keyword}
					<div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
						 on:click={() => viewKeywordDetail(keyword)}
						 role="button"
						 tabindex="0">
						<div class="flex items-start justify-between">
							<div class="flex items-start space-x-3">
								<span class="inline-flex items-center justify-center w-8 h-8 rounded-full 
									{keyword.rank <= 3 ? 'bg-yellow-100 text-yellow-800' : 
									 keyword.rank <= 10 ? 'bg-blue-100 text-blue-800' : 
									 'bg-gray-100 text-gray-800'}">
									{keyword.rank}
								</span>
								<div class="flex-1 min-w-0">
									<div class="flex items-center">
										<Hash class="w-4 h-4 text-gray-400 mr-1" />
										<h3 class="text-sm font-medium text-gray-900">{keyword.keyword}</h3>
									</div>
									<div class="flex items-center mt-1 space-x-2">
										<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium 
											bg-{getPlatformColor(keyword.platform)}-100 text-{getPlatformColor(keyword.platform)}-800">
											{getPlatformIcon(keyword.platform)} {keyword.platform.toUpperCase()}
										</span>
										<span class="text-xs text-gray-500">{keyword.search_volume ? formatScore(keyword.search_volume) : 'N/A'}</span>
										{#if keyword.change_percentage}
											<span class="text-xs text-green-600">{keyword.change_percentage}</span>
										{/if}
									</div>
									<div class="flex items-center mt-1 text-xs text-gray-500">
										<Clock class="w-3 h-3 mr-1" />
										{getPeriodLabel(keyword.period)} • {keyword.region} • {formatDate(keyword.collected_at)}
									</div>
								</div>
							</div>
							<Eye class="w-4 h-4 text-gray-400" />
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
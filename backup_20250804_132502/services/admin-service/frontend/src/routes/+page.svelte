<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$utils/api';
	import { formatNumber, formatDateTime, getStatusColor } from '$utils/helpers';
	import toast from 'svelte-french-toast';
	import { 
		Activity, 
		Users, 
		Globe, 
		TrendingUp, 
		AlertCircle, 
		CheckCircle, 
		Clock,
		Server,
		Database,
		Cpu
	} from 'lucide-svelte';

	let loading = true;
	let stats: any = {};
	let recentLogs: any[] = [];
	let systemHealth: any = {};

	onMount(async () => {
		await Promise.all([
			loadDashboardStats(),
			loadRecentLogs(),
			loadSystemHealth()
		]);
		loading = false;
	});

	async function loadDashboardStats() {
		try {
			const response = await apiClient.dashboard.stats();
			stats = response.data;
		} catch (error) {
			console.error('載入統計數據失敗:', error);
			toast.error('載入統計數據失敗');
		}
	}

	async function loadRecentLogs() {
		try {
			const response = await apiClient.logs.list({ 
				limit: 10, 
				sort_by: 'created_at',
				sort_order: 'desc'
			});
			recentLogs = response.data.items || [];
		} catch (error) {
			console.error('載入日誌失敗:', error);
		}
	}

	async function loadSystemHealth() {
		try {
			const response = await apiClient.health();
			systemHealth = response.data;
		} catch (error) {
			console.error('載入系統狀態失敗:', error);
		}
	}

	// 模擬數據（如果 API 尚未實現）
	$: if (!loading && Object.keys(stats).length === 0) {
		stats = {
			total_ai_providers: 5,
			active_ai_providers: 4,
			total_crawlers: 12,
			running_crawlers: 3,
			total_keywords: 1250,
			trending_keywords_24h: 89,
			total_logs: 54230,
			error_logs_24h: 12
		};

		recentLogs = [
			{
				id: 1,
				level: 'info',
				message: 'YouTube 趨勢爬蟲任務完成',
				created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
				source: 'crawler'
			},
			{
				id: 2,
				level: 'warning',
				message: 'OpenAI API 連接超時',
				created_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
				source: 'ai_provider'
			},
			{
				id: 3,
				level: 'success',
				message: '新增 AI Provider 配置成功',
				created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
				source: 'system'
			}
		];

		systemHealth = {
			status: 'healthy',
			api_status: 'healthy',
			database_status: 'healthy',
			celery_status: 'healthy',
			redis_status: 'healthy',
			cpu_usage: 35,
			memory_usage: 68,
			disk_usage: 45
		};
	}

	function getHealthStatusColor(status: string): string {
		return status === 'healthy' ? 'text-green-600' : 'text-red-600';
	}

	function getUsageColor(usage: number): string {
		if (usage < 70) return 'bg-green-500';
		if (usage < 85) return 'bg-yellow-500';
		return 'bg-red-500';
	}
</script>

<svelte:head>
	<title>儀表板 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div>
		<h1 class="text-2xl font-semibold text-gray-900">儀表板</h1>
		<p class="mt-2 text-sm text-gray-700">系統概覽和關鍵指標</p>
	</div>

	{#if loading}
		<!-- 載入中狀態 -->
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
			<span class="ml-2 text-gray-600">載入中...</span>
		</div>
	{:else}
		<!-- 統計卡片 -->
		<div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
			<!-- AI Providers -->
			<div class="card">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
								<Activity class="w-5 h-5 text-white" />
							</div>
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="text-sm font-medium text-gray-500 truncate">AI Providers</dt>
								<dd class="flex items-baseline">
									<div class="text-2xl font-semibold text-gray-900">
										{formatNumber(stats.active_ai_providers || 0)}
									</div>
									<div class="ml-2 text-sm text-gray-500">
										/ {formatNumber(stats.total_ai_providers || 0)}
									</div>
								</dd>
							</dl>
						</div>
					</div>
				</div>
				<div class="bg-gray-50 px-5 py-3">
					<div class="text-sm">
						<a href="/ai-providers" class="font-medium text-primary-600 hover:text-primary-500">
							查看詳情
						</a>
					</div>
				</div>
			</div>

			<!-- 爬蟲配置 -->
			<div class="card">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
								<Globe class="w-5 h-5 text-white" />
							</div>
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="text-sm font-medium text-gray-500 truncate">爬蟲任務</dt>
								<dd class="flex items-baseline">
									<div class="text-2xl font-semibold text-gray-900">
										{formatNumber(stats.running_crawlers || 0)}
									</div>
									<div class="ml-2 text-sm text-gray-500">
										/ {formatNumber(stats.total_crawlers || 0)}
									</div>
								</dd>
							</dl>
						</div>
					</div>
				</div>
				<div class="bg-gray-50 px-5 py-3">
					<div class="text-sm">
						<a href="/crawlers" class="font-medium text-primary-600 hover:text-primary-500">
							查看詳情
						</a>
					</div>
				</div>
			</div>

			<!-- 熱門關鍵字 -->
			<div class="card">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
								<TrendingUp class="w-5 h-5 text-white" />
							</div>
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="text-sm font-medium text-gray-500 truncate">熱門關鍵字</dt>
								<dd class="flex items-baseline">
									<div class="text-2xl font-semibold text-gray-900">
										{formatNumber(stats.trending_keywords_24h || 0)}
									</div>
									<div class="ml-2 text-sm text-gray-500">24小時</div>
								</dd>
							</dl>
						</div>
					</div>
				</div>
				<div class="bg-gray-50 px-5 py-3">
					<div class="text-sm">
						<a href="/trends" class="font-medium text-primary-600 hover:text-primary-500">
							查看詳情
						</a>
					</div>
				</div>
			</div>

			<!-- 系統日誌 -->
			<div class="card">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<div class="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
								<AlertCircle class="w-5 h-5 text-white" />
							</div>
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="text-sm font-medium text-gray-500 truncate">錯誤日誌</dt>
								<dd class="flex items-baseline">
									<div class="text-2xl font-semibold text-gray-900">
										{formatNumber(stats.error_logs_24h || 0)}
									</div>
									<div class="ml-2 text-sm text-gray-500">24小時</div>
								</dd>
							</dl>
						</div>
					</div>
				</div>
				<div class="bg-gray-50 px-5 py-3">
					<div class="text-sm">
						<a href="/logs" class="font-medium text-primary-600 hover:text-primary-500">
							查看詳情
						</a>
					</div>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<!-- 系統健康狀態 -->
			<div class="card">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 flex items-center">
						<Server class="w-5 h-5 mr-2" />
						系統健康狀態
					</h3>
					<div class="mt-5 space-y-4">
						<!-- 服務狀態 -->
						<div class="grid grid-cols-2 gap-4">
							<div class="flex items-center justify-between">
								<span class="text-sm text-gray-500">API 服務</span>
								<span class="text-sm font-medium {getHealthStatusColor(systemHealth.api_status)}">
									{systemHealth.api_status === 'healthy' ? '正常' : '異常'}
								</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-gray-500">資料庫</span>
								<span class="text-sm font-medium {getHealthStatusColor(systemHealth.database_status)}">
									{systemHealth.database_status === 'healthy' ? '正常' : '異常'}
								</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-gray-500">Celery</span>
								<span class="text-sm font-medium {getHealthStatusColor(systemHealth.celery_status)}">
									{systemHealth.celery_status === 'healthy' ? '正常' : '異常'}
								</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-gray-500">Redis</span>
								<span class="text-sm font-medium {getHealthStatusColor(systemHealth.redis_status)}">
									{systemHealth.redis_status === 'healthy' ? '正常' : '異常'}
								</span>
							</div>
						</div>

						<!-- 資源使用率 -->
						<div class="space-y-3 pt-4 border-t border-gray-200">
							<div>
								<div class="flex items-center justify-between text-sm">
									<span class="text-gray-500">CPU 使用率</span>
									<span class="font-medium">{systemHealth.cpu_usage}%</span>
								</div>
								<div class="mt-1 w-full bg-gray-200 rounded-full h-2">
									<div class="h-2 {getUsageColor(systemHealth.cpu_usage)} rounded-full" style="width: {systemHealth.cpu_usage}%"></div>
								</div>
							</div>
							<div>
								<div class="flex items-center justify-between text-sm">
									<span class="text-gray-500">記憶體使用率</span>
									<span class="font-medium">{systemHealth.memory_usage}%</span>
								</div>
								<div class="mt-1 w-full bg-gray-200 rounded-full h-2">
									<div class="h-2 {getUsageColor(systemHealth.memory_usage)} rounded-full" style="width: {systemHealth.memory_usage}%"></div>
								</div>
							</div>
							<div>
								<div class="flex items-center justify-between text-sm">
									<span class="text-gray-500">磁碟使用率</span>
									<span class="font-medium">{systemHealth.disk_usage}%</span>
								</div>
								<div class="mt-1 w-full bg-gray-200 rounded-full h-2">
									<div class="h-2 {getUsageColor(systemHealth.disk_usage)} rounded-full" style="width: {systemHealth.disk_usage}%"></div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 最近日誌 -->
			<div class="card">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 flex items-center">
						<Activity class="w-5 h-5 mr-2" />
						最近活動
					</h3>
					<div class="mt-5">
						{#if recentLogs.length > 0}
							<div class="flow-root">
								<ul class="-mb-8">
									{#each recentLogs as log, index}
										<li>
											<div class="relative pb-8">
												{#if index !== recentLogs.length - 1}
													<span class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"></span>
												{/if}
												<div class="relative flex space-x-3">
													<div>
														<span class="h-8 w-8 rounded-full flex items-center justify-center {
															log.level === 'error' ? 'bg-red-500' :
															log.level === 'warning' ? 'bg-yellow-500' :
															log.level === 'success' ? 'bg-green-500' :
															'bg-blue-500'
														}">
															{#if log.level === 'error'}
																<AlertCircle class="w-4 h-4 text-white" />
															{:else if log.level === 'success'}
																<CheckCircle class="w-4 h-4 text-white" />
															{:else}
																<Clock class="w-4 h-4 text-white" />
															{/if}
														</span>
													</div>
													<div class="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
														<div>
															<p class="text-sm text-gray-500">{log.message}</p>
														</div>
														<div class="text-right text-sm whitespace-nowrap text-gray-500">
															{formatDateTime(log.created_at)}
														</div>
													</div>
												</div>
											</div>
										</li>
									{/each}
								</ul>
							</div>
						{:else}
							<p class="text-sm text-gray-500">暫無活動記錄</p>
						{/if}
					</div>
					<div class="mt-6">
						<a href="/logs" class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
							查看所有日誌
						</a>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
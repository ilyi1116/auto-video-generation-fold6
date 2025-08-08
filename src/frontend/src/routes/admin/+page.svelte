<script>
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api/client.js';

	let stats = {
		totalUsers: 0,
		totalVideos: 0,
		activeVideos: 0,
		completedVideos: 0
	};
	
	let mockDataStats = {
		test_users_count: 0,
		video_templates_count: 0,
		sample_videos_count: 0,
		voice_options_count: 0
	};

	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			// 獲取一般統計資料
			const dashboardResponse = await apiClient.get('/api/v1/analytics/dashboard');
			if (dashboardResponse.success) {
				stats = dashboardResponse.data;
			}

			// 獲取假資料統計
			const mockStatsResponse = await apiClient.get('/api/v1/mock-data/stats');
			if (mockStatsResponse.success) {
				mockDataStats = mockStatsResponse.data;
			}

		} catch (err) {
			error = err.message;
			console.error('載入儀表板數據失敗:', err);
		} finally {
			loading = false;
		}
	});

	// 統計卡片資料
	$: dashboardCards = [
		{
			title: '總用戶數',
			value: stats.totalUsers || 0,
			icon: '👥',
			color: 'blue',
			description: '平台註冊用戶總數'
		},
		{
			title: '總影片數',
			value: stats.totalVideos || 0,
			icon: '🎬',
			color: 'green',
			description: '已創建的影片專案'
		},
		{
			title: '處理中影片',
			value: stats.activeVideos || 0,
			icon: '⚡',
			color: 'yellow',
			description: '正在生成的影片'
		},
		{
			title: '完成影片',
			value: stats.completedVideos || 0,
			icon: '✅',
			color: 'purple',
			description: '已完成的影片專案'
		}
	];

	$: mockDataCards = [
		{
			title: '測試用戶',
			value: mockDataStats.test_users_count,
			icon: '🧪',
			color: 'indigo'
		},
		{
			title: '影片模板',
			value: mockDataStats.video_templates_count,
			icon: '📝',
			color: 'pink'
		},
		{
			title: '範例影片',
			value: mockDataStats.sample_videos_count,
			icon: '🎭',
			color: 'orange'
		},
		{
			title: '語音選項',
			value: mockDataStats.voice_options_count,
			icon: '🎤',
			color: 'teal'
		}
	];

	function getColorClasses(color) {
		const colors = {
			blue: 'bg-blue-500 text-blue-100',
			green: 'bg-green-500 text-green-100',
			yellow: 'bg-yellow-500 text-yellow-100',
			purple: 'bg-purple-500 text-purple-100',
			indigo: 'bg-indigo-500 text-indigo-100',
			pink: 'bg-pink-500 text-pink-100',
			orange: 'bg-orange-500 text-orange-100',
			teal: 'bg-teal-500 text-teal-100'
		};
		return colors[color] || 'bg-gray-500 text-gray-100';
	}
</script>

<svelte:head>
	<title>管理後台 - Auto Video Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題 -->
	<div>
		<h1 class="text-2xl font-bold text-gray-900">管理後台儀表板</h1>
		<p class="text-gray-600">系統概覽和快速統計</p>
	</div>

	{#if loading}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
			<span class="ml-2 text-gray-600">載入中...</span>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4">
			<div class="flex">
				<div class="text-red-400 text-lg mr-3">⚠️</div>
				<div>
					<h3 class="text-red-800 font-medium">載入失敗</h3>
					<p class="text-red-700 text-sm">{error}</p>
				</div>
			</div>
		</div>
	{:else}
		<!-- 系統統計 -->
		<section>
			<h2 class="text-lg font-semibold text-gray-900 mb-4">系統統計</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				{#each dashboardCards as card}
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<div class="flex items-center">
							<div class="p-3 rounded-lg {getColorClasses(card.color)}">
								<span class="text-2xl">{card.icon}</span>
							</div>
							<div class="ml-4">
								<p class="text-sm font-medium text-gray-600">{card.title}</p>
								<p class="text-2xl font-bold text-gray-900">{card.value.toLocaleString()}</p>
								{#if card.description}
									<p class="text-xs text-gray-500 mt-1">{card.description}</p>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- 假資料統計 -->
		<section>
			<h2 class="text-lg font-semibold text-gray-900 mb-4">假資料統計</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
				{#each mockDataCards as card}
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<div class="flex items-center">
							<div class="p-3 rounded-lg {getColorClasses(card.color)}">
								<span class="text-2xl">{card.icon}</span>
							</div>
							<div class="ml-4">
								<p class="text-sm font-medium text-gray-600">{card.title}</p>
								<p class="text-2xl font-bold text-gray-900">{card.value}</p>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- 快速操作 -->
		<section>
			<h2 class="text-lg font-semibold text-gray-900 mb-4">快速操作</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				<!-- 假資料管理 -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center mb-4">
						<span class="text-2xl mr-3">🗃️</span>
						<h3 class="text-lg font-medium text-gray-900">假資料管理</h3>
					</div>
					<p class="text-gray-600 text-sm mb-4">管理測試用戶、影片模板和AI回應範例</p>
					<a 
						href="/admin/mock-data"
						class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
					>
						開始管理
						<span class="ml-2">→</span>
					</a>
				</div>

				<!-- 用戶管理 -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center mb-4">
						<span class="text-2xl mr-3">👥</span>
						<h3 class="text-lg font-medium text-gray-900">用戶管理</h3>
					</div>
					<p class="text-gray-600 text-sm mb-4">查看和管理平台用戶，設定權限和狀態</p>
					<a 
						href="/admin/users"
						class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
					>
						管理用戶
						<span class="ml-2">→</span>
					</a>
				</div>

				<!-- 系統設定 -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center mb-4">
						<span class="text-2xl mr-3">⚙️</span>
						<h3 class="text-lg font-medium text-gray-900">系統設定</h3>
					</div>
					<p class="text-gray-600 text-sm mb-4">配置系統參數、API金鑰和平台設定</p>
					<a 
						href="/admin/settings"
						class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700"
					>
						系統設定
						<span class="ml-2">→</span>
					</a>
				</div>
			</div>
		</section>

		<!-- 最近活動 -->
		<section>
			<h2 class="text-lg font-semibold text-gray-900 mb-4">系統狀態</h2>
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
					<!-- API Gateway狀態 -->
					<div class="flex items-center">
						<div class="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
						<div>
							<p class="font-medium text-gray-900">API Gateway</p>
							<p class="text-sm text-gray-600">運行正常</p>
						</div>
					</div>

					<!-- 資料庫狀態 -->
					<div class="flex items-center">
						<div class="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
						<div>
							<p class="font-medium text-gray-900">資料庫</p>
							<p class="text-sm text-gray-600">連接正常</p>
						</div>
					</div>

					<!-- AI服務狀態 -->
					<div class="flex items-center">
						<div class="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
						<div>
							<p class="font-medium text-gray-900">AI服務</p>
							<p class="text-sm text-gray-600">運行正常</p>
						</div>
					</div>
				</div>
			</div>
		</section>
	{/if}
</div>
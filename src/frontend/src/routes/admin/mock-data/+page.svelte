<script>
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/utils/api.js';
	import { toastStore } from '$lib/stores/toast.js';

	let currentTab = 'users';
	let loading = false;
	let error = null;

	// 資料狀態
	let users = [];
	let videoTemplates = [];
	let sampleVideos = [];
	let voiceOptions = [];
	let categories = [];
	let stats = {};

	// 編輯狀態
	let editingItem = null;
	let showAddModal = false;

	onMount(async () => {
		await loadStats();
		await loadData();
	});

	async function loadStats() {
		try {
			const response = await apiClient.get('/api/v1/mock-data/stats');
			if (response.success) {
				stats = response.data;
			}
		} catch (err) {
			console.error('載入統計失敗:', err);
		}
	}

	async function loadData() {
		loading = true;
		error = null;
		
		try {
			const responses = await Promise.all([
				apiClient.get('/api/v1/mock-data/users'),
				apiClient.get('/api/v1/mock-data/video-templates'),
				apiClient.get('/api/v1/mock-data/sample-videos'),
				apiClient.get('/api/v1/mock-data/voice-options'),
				apiClient.get('/api/v1/mock-data/categories')
			]);

			if (responses[0].success) users = responses[0].data;
			if (responses[1].success) videoTemplates = responses[1].data;
			if (responses[2].success) sampleVideos = responses[2].data;
			if (responses[3].success) voiceOptions = responses[3].data;
			if (responses[4].success) categories = responses[4].data;

		} catch (err) {
			error = err.message;
			toastStore.error('載入假資料失敗: ' + err.message);
		} finally {
			loading = false;
		}
	}

	async function clearCache() {
		try {
			const response = await apiClient.delete('/api/v1/mock-data/cache');
			if (response.success) {
				toastStore.success('快取已清除');
				await loadData();
			}
		} catch (err) {
			toastStore.error('清除快取失敗: ' + err.message);
		}
	}

	function handleTabChange(tab) {
		currentTab = tab;
	}

	function editItem(item) {
		editingItem = { ...item };
		showAddModal = true;
	}

	function addNewItem() {
		editingItem = {};
		showAddModal = true;
	}

	function closeModal() {
		showAddModal = false;
		editingItem = null;
	}

	// 獲取狀態對應的中文和顏色
	function getStatusInfo(status) {
		const statusMap = {
			'PENDING': { text: '待處理', color: 'gray' },
			'GENERATING_SCRIPT': { text: '生成腳本中', color: 'blue' },
			'GENERATING_IMAGES': { text: '生成圖片中', color: 'purple' },
			'GENERATING_VOICE': { text: '生成語音中', color: 'green' },
			'COMPOSITING': { text: '合成中', color: 'orange' },
			'COMPLETED': { text: '已完成', color: 'green' },
			'FAILED': { text: '失敗', color: 'red' }
		};
		return statusMap[status] || { text: status, color: 'gray' };
	}

	function getStatusColor(color) {
		const colors = {
			gray: 'bg-gray-100 text-gray-800',
			blue: 'bg-blue-100 text-blue-800',
			purple: 'bg-purple-100 text-purple-800',
			green: 'bg-green-100 text-green-800',
			orange: 'bg-orange-100 text-orange-800',
			red: 'bg-red-100 text-red-800'
		};
		return colors[color] || colors.gray;
	}

	const tabs = [
		{ id: 'users', name: '測試用戶', icon: '👥', count: stats.test_users_count },
		{ id: 'templates', name: '影片模板', icon: '📝', count: stats.video_templates_count },
		{ id: 'samples', name: '範例影片', icon: '🎬', count: stats.sample_videos_count },
		{ id: 'voices', name: '語音選項', icon: '🎤', count: stats.voice_options_count },
		{ id: 'categories', name: '內容分類', icon: '📂', count: categories.length }
	];
</script>

<svelte:head>
	<title>假資料管理 - Auto Video Platform</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題和操作 -->
	<div class="flex justify-between items-center">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">假資料管理</h1>
			<p class="text-gray-600">管理測試資料、模板和範例內容</p>
		</div>
		
		<div class="flex space-x-3">
			<button
				on:click={clearCache}
				class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
			>
				🔄 清除快取
			</button>
			
			<button
				on:click={addNewItem}
				class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
			>
				➕ 新增項目
			</button>
		</div>
	</div>

	<!-- 統計卡片 -->
	<div class="grid grid-cols-1 md:grid-cols-5 gap-4">
		{#each tabs as tab}
			<div class="bg-white p-4 rounded-lg border border-gray-200">
				<div class="flex items-center">
					<span class="text-2xl mr-2">{tab.icon}</span>
					<div>
						<p class="text-sm text-gray-600">{tab.name}</p>
						<p class="text-xl font-bold text-gray-900">{tab.count || 0}</p>
					</div>
				</div>
			</div>
		{/each}
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
		<!-- 標籤選擇 -->
		<div class="border-b border-gray-200">
			<nav class="-mb-px flex space-x-8">
				{#each tabs as tab}
					<button
						on:click={() => handleTabChange(tab.id)}
						class="py-2 px-1 border-b-2 font-medium text-sm {
							currentTab === tab.id
								? 'border-blue-500 text-blue-600'
								: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
						}"
					>
						<span class="mr-2">{tab.icon}</span>
						{tab.name}
						{#if tab.count}
							<span class="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2 rounded-full text-xs">
								{tab.count}
							</span>
						{/if}
					</button>
				{/each}
			</nav>
		</div>

		<!-- 內容區域 -->
		<div class="bg-white rounded-lg border border-gray-200">
			{#if currentTab === 'users'}
				<!-- 測試用戶 -->
				<div class="p-6">
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										用戶
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										角色
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										狀態
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										操作
									</th>
								</tr>
							</thead>
							<tbody class="bg-white divide-y divide-gray-200">
								{#each users as user}
									<tr class="hover:bg-gray-50">
										<td class="px-6 py-4 whitespace-nowrap">
											<div class="flex items-center">
												<div class="flex-shrink-0 h-10 w-10">
													<div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
														<span class="text-sm font-medium text-blue-600">
															{user.full_name?.charAt(0) || '?'}
														</span>
													</div>
												</div>
												<div class="ml-4">
													<div class="text-sm font-medium text-gray-900">{user.full_name}</div>
													<div class="text-sm text-gray-500">{user.email}</div>
												</div>
											</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {
												user.role === 'ADMIN' 
													? 'bg-purple-100 text-purple-800' 
													: 'bg-green-100 text-green-800'
											}">
												{user.role === 'ADMIN' ? '管理員' : '一般用戶'}
											</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {
												user.is_active 
													? 'bg-green-100 text-green-800' 
													: 'bg-red-100 text-red-800'
											}">
												{user.is_active ? '活躍' : '停用'}
											</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
											<button
												on:click={() => editItem(user)}
												class="text-blue-600 hover:text-blue-900 mr-4"
											>
												編輯
											</button>
											<button class="text-red-600 hover:text-red-900">
												刪除
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if currentTab === 'templates'}
				<!-- 影片模板 -->
				<div class="p-6">
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
						{#each videoTemplates as template}
							<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
								<div class="flex justify-between items-start mb-3">
									<h3 class="text-lg font-medium text-gray-900">{template.title}</h3>
									<span class="inline-flex px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
										{template.platform}
									</span>
								</div>
								<p class="text-sm text-gray-600 mb-3">{template.description}</p>
								<div class="flex flex-wrap gap-2 mb-3">
									{#each template.tags || [] as tag}
										<span class="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
											{tag}
										</span>
									{/each}
								</div>
								<div class="flex justify-between items-center text-sm text-gray-500">
									<span>{template.style}</span>
									<span>{template.duration_seconds}秒</span>
								</div>
								<div class="mt-4 flex justify-end space-x-2">
									<button
										on:click={() => editItem(template)}
										class="text-blue-600 hover:text-blue-900 text-sm"
									>
										編輯
									</button>
									<button class="text-red-600 hover:text-red-900 text-sm">
										刪除
									</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else if currentTab === 'samples'}
				<!-- 範例影片 -->
				<div class="p-6">
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										影片
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										狀態
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										平台
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										進度
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										操作
									</th>
								</tr>
							</thead>
							<tbody class="bg-white divide-y divide-gray-200">
								{#each sampleVideos as video}
									<tr class="hover:bg-gray-50">
										<td class="px-6 py-4">
											<div class="flex items-center">
												<div class="flex-shrink-0 h-16 w-24 bg-gray-200 rounded overflow-hidden">
													{#if video.thumbnail_url}
														<img src={video.thumbnail_url} alt={video.title} class="h-full w-full object-cover">
													{:else}
														<div class="h-full w-full flex items-center justify-center text-gray-400">
															🎬
														</div>
													{/if}
												</div>
												<div class="ml-4">
													<div class="text-sm font-medium text-gray-900">{video.title}</div>
													<div class="text-sm text-gray-500">{video.description}</div>
													<div class="text-xs text-gray-400">{video.duration_seconds}秒</div>
												</div>
											</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											{@const statusInfo = getStatusInfo(video.status)}
											<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(statusInfo.color)}">
												{statusInfo.text}
											</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="text-sm text-gray-900">{video.platform}</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<div class="flex items-center">
												<div class="w-16 bg-gray-200 rounded-full h-2">
													<div class="bg-blue-500 h-2 rounded-full" style="width: {video.progress_percentage || 0}%"></div>
												</div>
												<span class="ml-2 text-sm text-gray-600">{video.progress_percentage || 0}%</span>
											</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
											<button
												on:click={() => editItem(video)}
												class="text-blue-600 hover:text-blue-900 mr-4"
											>
												編輯
											</button>
											<button class="text-red-600 hover:text-red-900">
												刪除
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if currentTab === 'voices'}
				<!-- 語音選項 -->
				<div class="p-6">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						{#each voiceOptions as voice}
							<div class="border border-gray-200 rounded-lg p-4">
								<div class="flex items-center mb-3">
									<div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
										<span class="text-white text-lg">🎤</span>
									</div>
									<div class="ml-4">
										<h3 class="text-lg font-medium text-gray-900">{voice.name}</h3>
										<p class="text-sm text-gray-500">{voice.voice_id}</p>
									</div>
								</div>
								<p class="text-sm text-gray-600 mb-3">{voice.description}</p>
								<div class="flex justify-between items-center text-sm text-gray-500">
									<span>年齡: {voice.age_range}</span>
									<span>音調: {voice.tone}</span>
								</div>
								<div class="mt-4 flex justify-end space-x-2">
									<button class="text-green-600 hover:text-green-900 text-sm">
										試聽
									</button>
									<button
										on:click={() => editItem(voice)}
										class="text-blue-600 hover:text-blue-900 text-sm"
									>
										編輯
									</button>
									<button class="text-red-600 hover:text-red-900 text-sm">
										刪除
									</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else if currentTab === 'categories'}
				<!-- 內容分類 -->
				<div class="p-6">
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
						{#each categories as category}
							<div class="border border-gray-200 rounded-lg p-4">
								<h3 class="text-lg font-medium text-gray-900 mb-2">{category.name}</h3>
								<p class="text-sm text-gray-600 mb-3">{category.description}</p>
								<div class="mb-3">
									<p class="text-xs text-gray-500 mb-2">關鍵字:</p>
									<div class="flex flex-wrap gap-1">
										{#each category.keywords || [] as keyword}
											<span class="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
												{keyword}
											</span>
										{/each}
									</div>
								</div>
								<div class="mb-3">
									<p class="text-xs text-gray-500 mb-2">適用平台:</p>
									<div class="flex flex-wrap gap-1">
										{#each category.target_platforms || [] as platform}
											<span class="inline-flex px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
												{platform}
											</span>
										{/each}
									</div>
								</div>
								<div class="flex justify-end space-x-2">
									<button
										on:click={() => editItem(category)}
										class="text-blue-600 hover:text-blue-900 text-sm"
									>
										編輯
									</button>
									<button class="text-red-600 hover:text-red-900 text-sm">
										刪除
									</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- 編輯/新增模態框 -->
{#if showAddModal}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
			<div class="flex justify-between items-center mb-4">
				<h3 class="text-lg font-medium text-gray-900">
					{editingItem.id ? '編輯' : '新增'} 項目
				</h3>
				<button
					on:click={closeModal}
					class="text-gray-400 hover:text-gray-600"
				>
					✕
				</button>
			</div>
			
			<!-- 編輯表單內容將根據當前標籤動態生成 -->
			<div class="space-y-4">
				<p class="text-gray-600">編輯表單功能開發中...</p>
				<div class="flex justify-end space-x-3">
					<button
						on:click={closeModal}
						class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
					>
						取消
					</button>
					<button
						class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
					>
						儲存
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$utils/api';
	import { formatDateTime, getStatusColor } from '$utils/helpers';
	import toast from 'svelte-french-toast';
	import { 
		Plus, 
		Search, 
		Filter, 
		Edit, 
		Trash2, 
		Play, 
		MoreVertical,
		CheckCircle,
		XCircle,
		AlertCircle
	} from 'lucide-svelte';

	let loading = true;
	let providers: any[] = [];
	let searchQuery = '';
	let filterStatus = 'all';
	let selectedProvider: any = null;
	let showDeleteModal = false;
	let testingProvider: number | null = null;

	// 分頁
	let currentPage = 1;
	let totalPages = 1;
	let totalItems = 0;
	const itemsPerPage = 10;

	onMount(() => {
		loadProviders();
	});

	async function loadProviders() {
		loading = true;
		try {
			const params = {
				page: currentPage,
				size: itemsPerPage,
				search: searchQuery || undefined,
				is_active: filterStatus === 'all' ? undefined : filterStatus === 'active'
			};

			const response = await apiClient.aiProviders.list(params);
			providers = response.data.items || [];
			totalItems = response.data.total || 0;
			totalPages = Math.ceil(totalItems / itemsPerPage);
		} catch (error) {
			console.error('載入 AI Providers 失敗:', error);
			toast.error('載入 AI Providers 失敗');
		} finally {
			loading = false;
		}
	}

	async function testProvider(id: number) {
		testingProvider = id;
		try {
			await apiClient.aiProviders.test(id);
			toast.success('AI Provider 測試成功');
			await loadProviders(); // 重新載入以更新狀態
		} catch (error: any) {
			console.error('測試 AI Provider 失敗:', error);
			toast.error(error.response?.data?.detail || '測試失敗');
		} finally {
			testingProvider = null;
		}
	}

	async function deleteProvider() {
		if (!selectedProvider) return;
		
		try {
			await apiClient.aiProviders.delete(selectedProvider.id);
			toast.success('AI Provider 刪除成功');
			showDeleteModal = false;
			selectedProvider = null;
			await loadProviders();
		} catch (error: any) {
			console.error('刪除 AI Provider 失敗:', error);
			toast.error(error.response?.data?.detail || '刪除失敗');
		}
	}

	function handleSearch() {
		currentPage = 1;
		loadProviders();
	}

	function handleFilterChange() {
		currentPage = 1;
		loadProviders();
	}

	function changePage(page: number) {
		currentPage = page;
		loadProviders();
	}

	function showDeleteConfirm(provider: any) {
		selectedProvider = provider;
		showDeleteModal = true;
	}

	function getProviderTypeLabel(type: string): string {
		const types: { [key: string]: string } = {
			'openai': 'OpenAI',
			'anthropic': 'Anthropic',
			'google': 'Google Gemini',
			'azure': 'Azure OpenAI',
			'huggingface': 'Hugging Face',
			'other': '其他'
		};
		return types[type] || type;
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'active':
				return CheckCircle;
			case 'inactive':
				return XCircle;
			default:
				return AlertCircle;
		}
	}

	// 模擬數據（如果 API 尚未實現）
	$: if (!loading && providers.length === 0 && searchQuery === '' && filterStatus === 'all') {
		providers = [
			{
				id: 1,
				name: 'OpenAI GPT-4',
				provider_type: 'openai',
				is_active: true,
				last_test_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
				test_status: 'success',
				created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
			},
			{
				id: 2,
				name: 'Anthropic Claude',
				provider_type: 'anthropic',
				is_active: true,
				last_test_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
				test_status: 'success',
				created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
			},
			{
				id: 3,
				name: 'Google Gemini Pro',
				provider_type: 'google',
				is_active: false,
				last_test_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
				test_status: 'failed',
				created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
			}
		];
		totalItems = 3;
		totalPages = 1;
	}
</script>

<svelte:head>
	<title>AI Provider 管理 - 後台管理系統</title>
</svelte:head>

<div class="space-y-6">
	<!-- 頁面標題和操作 -->
	<div class="sm:flex sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-semibold text-gray-900">AI Provider 管理</h1>
			<p class="mt-2 text-sm text-gray-700">管理 AI 服務提供商配置</p>
		</div>
		<div class="mt-4 sm:mt-0">
			<a
				href="/ai-providers/create"
				class="btn btn-primary"
			>
				<Plus class="w-4 h-4 mr-2" />
				新增 Provider
			</a>
		</div>
	</div>

	<!-- 搜索和篩選 -->
	<div class="card">
		<div class="p-4">
			<div class="sm:flex sm:items-center sm:space-x-4">
				<!-- 搜索框 -->
				<div class="flex-1">
					<div class="relative">
						<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
							<Search class="h-5 w-5 text-gray-400" />
						</div>
						<input
							type="text"
							class="form-input pl-10"
							placeholder="搜索 Provider 名稱..."
							bind:value={searchQuery}
							on:keypress={(e) => e.key === 'Enter' && handleSearch()}
						/>
					</div>
				</div>

				<!-- 狀態篩選 -->
				<div class="mt-3 sm:mt-0">
					<select 
						class="form-select"
						bind:value={filterStatus}
						on:change={handleFilterChange}
					>
						<option value="all">所有狀態</option>
						<option value="active">啟用</option>
						<option value="inactive">禁用</option>
					</select>
				</div>

				<!-- 搜索按鈕 -->
				<div class="mt-3 sm:mt-0">
					<button
						type="button"
						class="btn btn-outline"
						on:click={handleSearch}
					>
						<Search class="w-4 h-4 mr-2" />
						搜索
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Provider 列表 -->
	<div class="card">
		{#if loading}
			<div class="p-6 text-center">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
				<p class="mt-2 text-sm text-gray-500">載入中...</p>
			</div>
		{:else if providers.length === 0}
			<div class="p-6 text-center">
				<p class="text-gray-500">沒有找到 AI Provider</p>
				<a href="/ai-providers/create" class="mt-2 btn btn-primary">
					新增第一個 Provider
				</a>
			</div>
		{:else}
			<!-- 表格 -->
			<div class="overflow-hidden">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Provider
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								類型
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								狀態
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								最後測試
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								創建時間
							</th>
							<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
								操作
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each providers as provider}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div class="flex-shrink-0 h-8 w-8">
											<div class="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
												<span class="text-primary-600 font-medium text-sm">
													{provider.name.charAt(0)}
												</span>
											</div>
										</div>
										<div class="ml-4">
											<div class="text-sm font-medium text-gray-900">
												{provider.name}
											</div>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="text-sm text-gray-900">
										{getProviderTypeLabel(provider.provider_type)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<svelte:component 
											this={getStatusIcon(provider.is_active ? 'active' : 'inactive')} 
											class="w-4 h-4 mr-2 {provider.is_active ? 'text-green-500' : 'text-gray-400'}"
										/>
										<span class="text-sm {provider.is_active ? 'text-green-800' : 'text-gray-500'}">
											{provider.is_active ? '啟用' : '禁用'}
										</span>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									{#if provider.last_test_at}
										<div class="text-sm text-gray-900">
											{formatDateTime(provider.last_test_at)}
										</div>
										<div class="text-sm text-gray-500">
											<span class="badge {
												provider.test_status === 'success' ? 'badge-success' :
												provider.test_status === 'failed' ? 'badge-error' :
												'badge-warning'
											}">
												{provider.test_status === 'success' ? '成功' :
												 provider.test_status === 'failed' ? '失敗' : '未知'}
											</span>
										</div>
									{:else}
										<span class="text-sm text-gray-400">未測試</span>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDateTime(provider.created_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<div class="flex items-center justify-end space-x-2">
										<!-- 測試按鈕 -->
										<button
											class="text-blue-600 hover:text-blue-900 disabled:opacity-50"
											on:click={() => testProvider(provider.id)}
											disabled={testingProvider === provider.id}
											title="測試連接"
										>
											{#if testingProvider === provider.id}
												<div class="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
											{:else}
												<Play class="w-4 h-4" />
											{/if}
										</button>

										<!-- 編輯按鈕 -->
										<a
											href="/ai-providers/{provider.id}/edit"
											class="text-indigo-600 hover:text-indigo-900"
											title="編輯"
										>
											<Edit class="w-4 h-4" />
										</a>

										<!-- 刪除按鈕 -->
										<button
											class="text-red-600 hover:text-red-900"
											on:click={() => showDeleteConfirm(provider)}
											title="刪除"
										>
											<Trash2 class="w-4 h-4" />
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- 分頁 -->
			{#if totalPages > 1}
				<div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
					<div class="flex-1 flex justify-between sm:hidden">
						<button
							class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
							disabled={currentPage <= 1}
							on:click={() => changePage(currentPage - 1)}
						>
							上一頁
						</button>
						<button
							class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
							disabled={currentPage >= totalPages}
							on:click={() => changePage(currentPage + 1)}
						>
							下一頁
						</button>
					</div>
					<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
						<div>
							<p class="text-sm text-gray-700">
								顯示第 <span class="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
								到 <span class="font-medium">{Math.min(currentPage * itemsPerPage, totalItems)}</span>
								項，共 <span class="font-medium">{totalItems}</span> 項
							</p>
						</div>
						<div>
							<nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
								<button
									class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
									disabled={currentPage <= 1}
									on:click={() => changePage(currentPage - 1)}
								>
									上一頁
								</button>
								
								{#each Array.from({length: totalPages}, (_, i) => i + 1) as page}
									{#if page <= 5 || page > totalPages - 5 || Math.abs(page - currentPage) <= 2}
										<button
											class="relative inline-flex items-center px-4 py-2 border text-sm font-medium {
												page === currentPage 
													? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
													: 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
											}"
											on:click={() => changePage(page)}
										>
											{page}
										</button>
									{:else if page === 6 && currentPage > 8}
										<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
											...
										</span>
									{:else if page === totalPages - 5 && currentPage < totalPages - 7}
										<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
											...
										</span>
									{/if}
								{/each}
								
								<button
									class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
									disabled={currentPage >= totalPages}
									on:click={() => changePage(currentPage + 1)}
								>
									下一頁
								</button>
							</nav>
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<!-- 刪除確認模態框 -->
{#if showDeleteModal}
	<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" on:click={() => showDeleteModal = false}>
		<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" on:click|stopPropagation>
			<div class="mt-3 text-center">
				<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
					<Trash2 class="h-6 w-6 text-red-600" />
				</div>
				<h3 class="text-lg font-medium text-gray-900 mt-2">確認刪除</h3>
				<div class="mt-2 px-7 py-3">
					<p class="text-sm text-gray-500">
						您確定要刪除 AI Provider "{selectedProvider?.name}" 嗎？此操作無法撤銷。
					</p>
				</div>
				<div class="flex justify-center space-x-4 mt-4">
					<button
						class="btn btn-outline"
						on:click={() => showDeleteModal = false}
					>
						取消
					</button>
					<button
						class="btn btn-danger"
						on:click={deleteProvider}
					>
						確認刪除
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
<script>
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	// 狀態管理
	let models = writable([]);
	let selectedModel = writable(null);
	let modelStats = writable({});
	let loading = writable(true);
	let autoRefresh = writable(true);
	let refreshInterval = null;

	// 表單狀態
	let showCreateModal = false;
	let showTrainingModal = false;
	let showDeployModal = false;
	let showUploadModal = false;

	// 創建模型表單
	let createForm = {
		name: '',
		description: '',
		model_type: 'voice_clone',
		tags: ''
	};

	// 訓練表單
	let trainingForm = {
		dataset_path: '',
		epochs: 100,
		batch_size: 32,
		learning_rate: 0.001,
		optimizer: 'adam'
	};

	// 部署表單
	let deployForm = {
		version: '1.0.0',
		environment: 'production',
		cpu_limit: 2.0,
		memory_limit: 2048,
		replicas: 1
	};

	// 過濾選項
	let filters = {
		model_type: '',
		status: '',
		search: ''
	};

	// API 基礎 URL
	const API_BASE = '/admin/voice-models';

	// 獲取模型列表
	async function fetchModels() {
		try {
			const params = new URLSearchParams();
			if (filters.model_type) params.append('model_type', filters.model_type);
			if (filters.status) params.append('status', filters.status);
			
			const response = await fetch(`${API_BASE}?${params}`);
			const data = await response.json();
			
			if (data.success) {
				let modelList = data.data.models;
				
				// 應用搜索過濾
				if (filters.search) {
					const searchLower = filters.search.toLowerCase();
					modelList = modelList.filter(model => 
						model.name.toLowerCase().includes(searchLower) ||
						model.description.toLowerCase().includes(searchLower) ||
						model.model_id.toLowerCase().includes(searchLower)
					);
				}
				
				models.set(modelList);
			}
		} catch (error) {
			console.error('獲取模型列表失敗:', error);
		}
	}

	// 獲取模型統計
	async function fetchModelStats() {
		try {
			const response = await fetch(`${API_BASE}/stats/summary`);
			const data = await response.json();
			if (data.success) {
				modelStats.set(data.data);
			}
		} catch (error) {
			console.error('獲取模型統計失敗:', error);
		}
	}

	// 獲取模型詳情
	async function fetchModelDetails(modelId) {
		try {
			const response = await fetch(`${API_BASE}/${modelId}`);
			const data = await response.json();
			if (data.success) {
				selectedModel.set(data.data);
			}
		} catch (error) {
			console.error('獲取模型詳情失敗:', error);
		}
	}

	// 創建模型
	async function createModel() {
		if (!createForm.name) {
			alert('請輸入模型名稱');
			return;
		}

		try {
			const response = await fetch(`${API_BASE}/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					name: createForm.name,
					description: createForm.description,
					model_type: createForm.model_type,
					tags: createForm.tags ? createForm.tags.split(',').map(t => t.trim()) : []
				})
			});

			const data = await response.json();
			if (data.success) {
				alert('模型創建成功');
				showCreateModal = false;
				resetCreateForm();
				await fetchModels();
			} else {
				alert('創建失敗: ' + data.message);
			}
		} catch (error) {
			console.error('創建模型失敗:', error);
			alert('創建失敗');
		}
	}

	// 開始訓練
	async function startTraining(modelId) {
		try {
			const response = await fetch(`${API_BASE}/${modelId}/train`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(trainingForm)
			});

			const data = await response.json();
			if (data.success) {
				alert('開始訓練');
				showTrainingModal = false;
				await fetchModels();
			} else {
				alert('開始訓練失敗: ' + data.message);
			}
		} catch (error) {
			console.error('開始訓練失敗:', error);
			alert('開始訓練失敗');
		}
	}

	// 部署模型
	async function deployModel(modelId) {
		try {
			const response = await fetch(`${API_BASE}/${modelId}/deploy`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(deployForm)
			});

			const data = await response.json();
			if (data.success) {
				alert('模型部署成功');
				showDeployModal = false;
				await fetchModels();
			} else {
				alert('部署失敗: ' + data.message);
			}
		} catch (error) {
			console.error('部署模型失敗:', error);
			alert('部署失敗');
		}
	}

	// 刪除模型
	async function deleteModel(modelId, modelName) {
		if (!confirm(`確定要刪除模型 "${modelName}" 嗎？此操作不可撤銷。`)) {
			return;
		}

		try {
			const response = await fetch(`${API_BASE}/${modelId}`, {
				method: 'DELETE'
			});

			const data = await response.json();
			if (data.success) {
				alert('模型已刪除');
				await fetchModels();
			} else {
				alert('刪除失敗: ' + data.message);
			}
		} catch (error) {
			console.error('刪除模型失敗:', error);
			alert('刪除失敗');
		}
	}

	// 獲取所有數據
	async function fetchAllData() {
		loading.set(true);
		await Promise.all([
			fetchModels(),
			fetchModelStats()
		]);
		loading.set(false);
	}

	// 重置創建表單
	function resetCreateForm() {
		createForm = {
			name: '',
			description: '',
			model_type: 'voice_clone',
			tags: ''
		};
	}

	// 格式化時間
	function formatTime(timestamp) {
		if (!timestamp) return '未知';
		return new Date(timestamp).toLocaleString('zh-TW');
	}

	// 獲取狀態顏色
	function getStatusColor(status) {
		switch (status) {
			case 'training': return 'warning';
			case 'trained': return 'success';
			case 'ready': return 'info';
			case 'deployed': return 'primary';
			case 'failed': return 'danger';
			case 'archived': return 'secondary';
			default: return 'secondary';
		}
	}

	// 獲取類型標籤
	function getTypeLabel(type) {
		switch (type) {
			case 'tts': return '文本轉語音';
			case 'voice_clone': return '語音克隆';
			case 'voice_enhance': return '語音增強';
			case 'voice_convert': return '語音轉換';
			default: return type;
		}
	}

	// 設置自動刷新
	function setupAutoRefresh() {
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
		
		if ($autoRefresh) {
			refreshInterval = setInterval(fetchAllData, 30000); // 30秒刷新
		}
	}

	// 組件掛載
	onMount(() => {
		fetchAllData();
		setupAutoRefresh();

		return () => {
			if (refreshInterval) {
				clearInterval(refreshInterval);
			}
		};
	});

	// 監聽自動刷新設置變化
	$: if ($autoRefresh !== undefined) {
		setupAutoRefresh();
	}

	// 監聽過濾條件變化
	$: if (filters) {
		fetchModels();
	}
</script>

<svelte:head>
	<title>語音模型管理 - 後台管理</title>
</svelte:head>

<div class="models-dashboard">
	<div class="d-flex justify-content-between align-items-center mb-4">
		<h1>語音模型管理</h1>
		<div class="d-flex gap-2">
			<div class="form-check form-switch">
				<input 
					class="form-check-input" 
					type="checkbox" 
					id="autoRefresh"
					bind:checked={$autoRefresh}
				>
				<label class="form-check-label" for="autoRefresh">
					自動刷新 (30秒)
				</label>
			</div>
			<button class="btn btn-outline-primary" on:click={fetchAllData}>
				<i class="fas fa-sync-alt"></i> 刷新
			</button>
			<button class="btn btn-success" on:click={() => showCreateModal = true}>
				<i class="fas fa-plus"></i> 創建模型
			</button>
		</div>
	</div>

	{#if $loading}
		<div class="text-center py-5">
			<div class="spinner-border" role="status">
				<span class="visually-hidden">載入中...</span>
			</div>
		</div>
	{:else}
		<!-- 統計摘要 -->
		{#if $modelStats.total_models !== undefined}
			<div class="row mb-4">
				<div class="col-md-3">
					<div class="card border-primary">
						<div class="card-body text-center">
							<h3 class="text-primary">{$modelStats.total_models}</h3>
							<small class="text-muted">總模型數</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-success">
						<div class="card-body text-center">
							<h3 class="text-success">{$modelStats.status_distribution?.deployed || 0}</h3>
							<small class="text-muted">已部署</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-warning">
						<div class="card-body text-center">
							<h3 class="text-warning">{$modelStats.status_distribution?.training || 0}</h3>
							<small class="text-muted">訓練中</small>
						</div>
					</div>
				</div>
				<div class="col-md-3">
					<div class="card border-info">
						<div class="card-body text-center">
							<h3 class="text-info">{($modelStats.average_metrics?.accuracy * 100).toFixed(1)}%</h3>
							<small class="text-muted">平均準確率</small>
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- 過濾器 -->
		<div class="card mb-4">
			<div class="card-body">
				<div class="row">
					<div class="col-md-3">
						<label class="form-label">模型類型</label>
						<select class="form-select" bind:value={filters.model_type}>
							<option value="">全部類型</option>
							<option value="tts">文本轉語音</option>
							<option value="voice_clone">語音克隆</option>
							<option value="voice_enhance">語音增強</option>
							<option value="voice_convert">語音轉換</option>
						</select>
					</div>
					<div class="col-md-3">
						<label class="form-label">狀態</label>
						<select class="form-select" bind:value={filters.status}>
							<option value="">全部狀態</option>
							<option value="training">訓練中</option>
							<option value="trained">已訓練</option>
							<option value="ready">就緒</option>
							<option value="deployed">已部署</option>
							<option value="failed">失敗</option>
						</select>
					</div>
					<div class="col-md-6">
						<label class="form-label">搜索</label>
						<input 
							type="text" 
							class="form-control" 
							placeholder="搜索模型名稱、描述或ID..."
							bind:value={filters.search}
						>
					</div>
				</div>
			</div>
		</div>

		<!-- 模型列表 -->
		<div class="card">
			<div class="card-header">
				<h5 class="mb-0">模型列表 ({$models.length})</h5>
			</div>
			<div class="card-body">
				{#if $models.length === 0}
					<p class="text-muted text-center">暫無模型</p>
				{:else}
					<div class="table-responsive">
						<table class="table table-hover">
							<thead>
								<tr>
									<th>模型名稱</th>
									<th>類型</th>
									<th>狀態</th>
									<th>版本</th>
									<th>準確率</th>
									<th>創建時間</th>
									<th>操作</th>
								</tr>
							</thead>
							<tbody>
								{#each $models as model}
									<tr>
										<td>
											<div>
												<strong>{model.name}</strong>
												<br>
												<small class="text-muted">{model.model_id}</small>
											</div>
										</td>
										<td>
											<span class="badge bg-info">{getTypeLabel(model.model_type)}</span>
										</td>
										<td>
											<span class="badge bg-{getStatusColor(model.status)}">{model.status}</span>
										</td>
										<td>{model.version}</td>
										<td>
											{#if model.accuracy_score}
												{(model.accuracy_score * 100).toFixed(1)}%
											{:else}
												-
											{/if}
										</td>
										<td>{formatTime(model.created_at)}</td>
										<td>
											<div class="btn-group btn-group-sm">
												<button 
													class="btn btn-outline-info"
													on:click={() => fetchModelDetails(model.model_id)}
													title="查看詳情"
												>
													<i class="fas fa-eye"></i>
												</button>
												
												{#if model.status === 'training'}
													<button class="btn btn-outline-warning" disabled title="訓練中">
														<i class="fas fa-hourglass-half"></i>
													</button>
												{:else if model.status === 'trained' || model.status === 'ready'}
													<button 
														class="btn btn-outline-success"
														on:click={() => {
															deployForm.version = model.version;
															showDeployModal = true;
														}}
														title="部署模型"
													>
														<i class="fas fa-rocket"></i>
													</button>
												{/if}
												
												{#if model.status !== 'training' && model.status !== 'deployed'}
													<button 
														class="btn btn-outline-primary"
														on:click={() => showTrainingModal = true}
														title="開始訓練"
													>
														<i class="fas fa-play"></i>
													</button>
												{/if}
												
												<button 
													class="btn btn-outline-danger"
													on:click={() => deleteModel(model.model_id, model.name)}
													title="刪除模型"
												>
													<i class="fas fa-trash"></i>
												</button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<!-- 創建模型模態框 -->
{#if showCreateModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">創建新模型</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showCreateModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="mb-3">
						<label for="modelName" class="form-label">模型名稱 *</label>
						<input 
							type="text" 
							class="form-control" 
							id="modelName"
							bind:value={createForm.name}
							placeholder="輸入模型名稱"
						>
					</div>
					<div class="mb-3">
						<label for="modelDescription" class="form-label">模型描述</label>
						<textarea 
							class="form-control" 
							id="modelDescription"
							rows="3"
							bind:value={createForm.description}
							placeholder="輸入模型描述"
						></textarea>
					</div>
					<div class="mb-3">
						<label for="modelType" class="form-label">模型類型</label>
						<select class="form-select" id="modelType" bind:value={createForm.model_type}>
							<option value="tts">文本轉語音</option>
							<option value="voice_clone">語音克隆</option>
							<option value="voice_enhance">語音增強</option>
							<option value="voice_convert">語音轉換</option>
						</select>
					</div>
					<div class="mb-3">
						<label for="modelTags" class="form-label">標籤</label>
						<input 
							type="text" 
							class="form-control" 
							id="modelTags"
							bind:value={createForm.tags}
							placeholder="用逗號分隔多個標籤"
						>
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showCreateModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-success" 
						on:click={createModel}
					>
						<i class="fas fa-plus"></i> 創建模型
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<!-- 訓練模型模態框 -->
{#if showTrainingModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog modal-lg">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">開始訓練</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showTrainingModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="row">
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">數據集路徑</label>
								<input 
									type="text" 
									class="form-control" 
									bind:value={trainingForm.dataset_path}
									placeholder="/path/to/dataset"
								>
							</div>
						</div>
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">訓練輪數</label>
								<input 
									type="number" 
									class="form-control" 
									bind:value={trainingForm.epochs}
									min="1"
									max="1000"
								>
							</div>
						</div>
					</div>
					<div class="row">
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">批次大小</label>
								<input 
									type="number" 
									class="form-control" 
									bind:value={trainingForm.batch_size}
									min="1"
									max="256"
								>
							</div>
						</div>
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">學習率</label>
								<input 
									type="number" 
									class="form-control" 
									bind:value={trainingForm.learning_rate}
									step="0.0001"
									min="0.0001"
									max="1.0"
								>
							</div>
						</div>
					</div>
					<div class="mb-3">
						<label class="form-label">優化器</label>
						<select class="form-select" bind:value={trainingForm.optimizer}>
							<option value="adam">Adam</option>
							<option value="sgd">SGD</option>
							<option value="rmsprop">RMSprop</option>
						</select>
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showTrainingModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-warning" 
						on:click={() => startTraining('selected_model_id')}
					>
						<i class="fas fa-play"></i> 開始訓練
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<!-- 部署模型模態框 -->
{#if showDeployModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">部署模型</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showDeployModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="mb-3">
						<label class="form-label">模型版本</label>
						<input 
							type="text" 
							class="form-control" 
							bind:value={deployForm.version}
							readonly
						>
					</div>
					<div class="mb-3">
						<label class="form-label">部署環境</label>
						<select class="form-select" bind:value={deployForm.environment}>
							<option value="development">開發環境</option>
							<option value="staging">測試環境</option>
							<option value="production">生產環境</option>
						</select>
					</div>
					<div class="row">
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">CPU 限制</label>
								<input 
									type="number" 
									class="form-control" 
									bind:value={deployForm.cpu_limit}
									step="0.5"
									min="0.5"
									max="16"
								>
							</div>
						</div>
						<div class="col-md-6">
							<div class="mb-3">
								<label class="form-label">內存限制 (MB)</label>
								<input 
									type="number" 
									class="form-control" 
									bind:value={deployForm.memory_limit}
									step="256"
									min="256"
									max="16384"
								>
							</div>
						</div>
					</div>
					<div class="mb-3">
						<label class="form-label">副本數量</label>
						<input 
							type="number" 
							class="form-control" 
							bind:value={deployForm.replicas}
							min="1"
							max="10"
						>
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showDeployModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-primary" 
						on:click={() => deployModel('selected_model_id')}
					>
						<i class="fas fa-rocket"></i> 部署模型
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<style>
	.models-dashboard {
		padding: 1rem;
	}

	.card {
		box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
	}

	.card-header {
		font-weight: 600;
	}

	.spinner-border {
		width: 3rem;
		height: 3rem;
	}

	.modal {
		background: rgba(0, 0, 0, 0.5);
	}

	.btn-group-sm .btn {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}

	.table th {
		border-top: none;
		font-weight: 600;
	}
</style>
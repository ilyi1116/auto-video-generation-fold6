<script>
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	// 狀態管理
	let traces = writable([]);
	let analysisData = writable({});
	let healthData = writable({});
	let loading = writable(true);
	let autoRefresh = writable(true);
	let refreshInterval = null;

	// 視圖狀態
	let activeTab = 'traces'; // traces, analysis, health
	let showSearchModal = false;
	let showExportModal = false;

	// 查詢參數
	let searchParams = {
		trace_id: '',
		service_name: '',
		operation_category: '',
		hours: 24,
		limit: 100
	};

	// 分析參數
	let analysisParams = {
		service_name: '',
		hours: 24,
		interval_minutes: 60
	};

	// 導出參數
	let exportParams = {
		start_date: '',
		end_date: ''
	};

	// 搜索參數
	let searchQuery = '';

	// API 基礎 URL
	const API_BASE = '/admin/tracing';

	// 獲取追蹤資料
	async function fetchTraces() {
		try {
			const params = new URLSearchParams();
			if (searchParams.trace_id) params.append('trace_id', searchParams.trace_id);
			if (searchParams.service_name) params.append('service_name', searchParams.service_name);
			if (searchParams.operation_category) params.append('operation_category', searchParams.operation_category);
			params.append('hours', searchParams.hours);
			params.append('limit', searchParams.limit);

			const response = await fetch(`${API_BASE}?${params}`);
			const data = await response.json();

			if (data.success) {
				traces.set(data.data.traces);
			}
		} catch (error) {
			console.error('獲取追蹤資料失敗:', error);
		}
	}

	// 獲取分析資料
	async function fetchAnalysisData() {
		try {
			const [performance, errors, services, trends] = await Promise.all([
				fetch(`${API_BASE}/analysis/performance?hours=${analysisParams.hours}&service_name=${analysisParams.service_name || ''}`).then(r => r.json()),
				fetch(`${API_BASE}/analysis/errors?hours=${analysisParams.hours}`).then(r => r.json()),
				fetch(`${API_BASE}/analysis/services?hours=${analysisParams.hours}`).then(r => r.json()),
				fetch(`${API_BASE}/analysis/trends?hours=${analysisParams.hours}&interval_minutes=${analysisParams.interval_minutes}`).then(r => r.json())
			]);

			analysisData.set({
				performance: performance.success ? performance.data : {},
				errors: errors.success ? errors.data : {},
				services: services.success ? services.data : {},
				trends: trends.success ? trends.data : {}
			});
		} catch (error) {
			console.error('獲取分析資料失敗:', error);
		}
	}

	// 獲取健康資料
	async function fetchHealthData() {
		try {
			const [overall, slowOps, collectorStats] = await Promise.all([
				fetch(`${API_BASE}/health?hours=1`).then(r => r.json()),
				fetch(`${API_BASE}/analysis/slow-operations?hours=24&limit=10`).then(r => r.json()),
				fetch(`${API_BASE}/stats/collector`).then(r => r.json())
			]);

			healthData.set({
				overall: overall.success ? overall.data : {},
				slowOperations: slowOps.success ? slowOps.data.slow_operations : [],
				collectorStats: collectorStats.success ? collectorStats.data : {}
			});
		} catch (error) {
			console.error('獲取健康資料失敗:', error);
		}
	}

	// 獲取所有資料
	async function fetchAllData() {
		loading.set(true);
		await Promise.all([
			fetchTraces(),
			fetchAnalysisData(),
			fetchHealthData()
		]);
		loading.set(false);
	}

	// 搜索追蹤
	async function searchTraces() {
		if (!searchQuery.trim()) {
			alert('請輸入搜索關鍵字');
			return;
		}

		try {
			const params = new URLSearchParams();
			params.append('query', searchQuery);
			if (searchParams.service_name) params.append('service_name', searchParams.service_name);
			params.append('hours', searchParams.hours);
			params.append('limit', 50);

			const response = await fetch(`${API_BASE}/search?${params}`);
			const data = await response.json();

			if (data.success) {
				traces.set(data.data.traces);
				showSearchModal = false;
			} else {
				alert('搜索失敗: ' + data.message);
			}
		} catch (error) {
			console.error('搜索追蹤失敗:', error);
			alert('搜索失敗');
		}
	}

	// 導出追蹤資料
	async function exportTraces() {
		try {
			const params = new URLSearchParams();
			if (exportParams.start_date) params.append('start_date', exportParams.start_date);
			if (exportParams.end_date) params.append('end_date', exportParams.end_date);

			const response = await fetch(`${API_BASE}/export?${params}`, {
				method: 'POST'
			});
			const data = await response.json();

			if (data.success) {
				// 創建下載連結
				const blob = new Blob([data.data.content], { type: 'application/json' });
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = `traces_export_${Date.now()}.jsonl`;
				a.click();
				window.URL.revokeObjectURL(url);

				showExportModal = false;
				alert(`成功導出 ${data.data.exported_count} 條追蹤資料`);
			} else {
				alert('導出失敗: ' + data.message);
			}
		} catch (error) {
			console.error('導出追蹤資料失敗:', error);
			alert('導出失敗');
		}
	}

	// 清理舊資料
	async function cleanupOldTraces() {
		if (!confirm('確定要清理舊的追蹤資料嗎？此操作不可撤銷。')) {
			return;
		}

		try {
			const response = await fetch(`${API_BASE}/cleanup?days=7`, {
				method: 'DELETE'
			});
			const data = await response.json();

			if (data.success) {
				alert('成功清理舊追蹤資料');
				await fetchAllData();
			} else {
				alert('清理失敗: ' + data.message);
			}
		} catch (error) {
			console.error('清理追蹤資料失敗:', error);
			alert('清理失敗');
		}
	}

	// 格式化時間
	function formatTime(timestamp) {
		if (!timestamp) return '未知';
		return new Date(timestamp).toLocaleString('zh-TW');
	}

	// 格式化持續時間
	function formatDuration(ms) {
		if (!ms) return '-';
		if (ms < 1000) return `${ms.toFixed(1)}ms`;
		return `${(ms / 1000).toFixed(2)}s`;
	}

	// 獲取狀態顏色
	function getStatusColor(status) {
		switch (status) {
			case 'success': return 'success';
			case 'error': return 'danger';
			case 'warning': return 'warning';
			case 'active': return 'info';
			default: return 'secondary';
		}
	}

	// 獲取健康狀態顏色
	function getHealthColor(status) {
		switch (status) {
			case 'healthy': return 'success';
			case 'warning': return 'warning';
			case 'critical': return 'danger';
			default: return 'secondary';
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
</script>

<svelte:head>
	<title>分散式追蹤 - 後台管理</title>
</svelte:head>

<div class="tracing-dashboard">
	<div class="d-flex justify-content-between align-items-center mb-4">
		<h1>分散式追蹤</h1>
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
			<button class="btn btn-outline-info" on:click={() => showSearchModal = true}>
				<i class="fas fa-search"></i> 搜索
			</button>
			<button class="btn btn-outline-success" on:click={() => showExportModal = true}>
				<i class="fas fa-download"></i> 導出
			</button>
			<button class="btn btn-outline-warning" on:click={cleanupOldTraces}>
				<i class="fas fa-trash"></i> 清理
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
		<!-- 標籤導航 -->
		<ul class="nav nav-tabs mb-4">
			<li class="nav-item">
				<button 
					class="nav-link" 
					class:active={activeTab === 'traces'}
					on:click={() => activeTab = 'traces'}
				>
					<i class="fas fa-list"></i> 追蹤列表
				</button>
			</li>
			<li class="nav-item">
				<button 
					class="nav-link" 
					class:active={activeTab === 'analysis'}
					on:click={() => activeTab = 'analysis'}
				>
					<i class="fas fa-chart-line"></i> 性能分析
				</button>
			</li>
			<li class="nav-item">
				<button 
					class="nav-link" 
					class:active={activeTab === 'health'}
					on:click={() => activeTab = 'health'}
				>
					<i class="fas fa-heartbeat"></i> 系統健康
				</button>
			</li>
		</ul>

		<!-- 追蹤列表 -->
		{#if activeTab === 'traces'}
			<div class="tab-content">
				<!-- 過濾器 -->
				<div class="card mb-4">
					<div class="card-body">
						<div class="row">
							<div class="col-md-3">
								<label class="form-label">追蹤ID</label>
								<input 
									type="text" 
									class="form-control" 
									placeholder="輸入追蹤ID..."
									bind:value={searchParams.trace_id}
									on:change={fetchTraces}
								>
							</div>
							<div class="col-md-3">
								<label class="form-label">服務名稱</label>
								<input 
									type="text" 
									class="form-control" 
									placeholder="輸入服務名稱..."
									bind:value={searchParams.service_name}
									on:change={fetchTraces}
								>
							</div>
							<div class="col-md-2">
								<label class="form-label">操作類別</label>
								<select class="form-select" bind:value={searchParams.operation_category} on:change={fetchTraces}>
									<option value="">全部類別</option>
									<option value="http">HTTP</option>
									<option value="database">數據庫</option>
									<option value="async_task">異步任務</option>
									<option value="cache">緩存</option>
									<option value="io">I/O</option>
									<option value="other">其他</option>
								</select>
							</div>
							<div class="col-md-2">
								<label class="form-label">時間範圍</label>
								<select class="form-select" bind:value={searchParams.hours} on:change={fetchTraces}>
									<option value={1}>1小時</option>
									<option value={6}>6小時</option>
									<option value={24}>24小時</option>
									<option value={72}>3天</option>
									<option value={168}>7天</option>
								</select>
							</div>
							<div class="col-md-2">
								<label class="form-label">結果限制</label>
								<select class="form-select" bind:value={searchParams.limit} on:change={fetchTraces}>
									<option value={50}>50</option>
									<option value={100}>100</option>
									<option value={200}>200</option>
									<option value={500}>500</option>
								</select>
							</div>
						</div>
					</div>
				</div>

				<!-- 追蹤表格 -->
				<div class="card">
					<div class="card-header">
						<h5 class="mb-0">追蹤記錄 ({$traces.length})</h5>
					</div>
					<div class="card-body">
						{#if $traces.length === 0}
							<p class="text-muted text-center">暫無追蹤資料</p>
						{:else}
							<div class="table-responsive">
								<table class="table table-hover">
									<thead>
										<tr>
											<th>追蹤ID</th>
											<th>服務</th>
											<th>操作</th>
											<th>狀態</th>
											<th>持續時間</th>
											<th>時間</th>
											<th>詳情</th>
										</tr>
									</thead>
									<tbody>
										{#each $traces as trace}
											<tr>
												<td>
													<code class="small">{trace.trace_id.slice(0, 8)}...</code>
												</td>
												<td>
													<span class="badge bg-info">{trace.service_name}</span>
												</td>
												<td>
													<div>
														<strong>{trace.operation_name || 'Unknown'}</strong>
														<br>
														<small class="text-muted">{trace.operation_category}</small>
													</div>
												</td>
												<td>
													<span class="badge bg-{getStatusColor(trace.status)}">{trace.status}</span>
												</td>
												<td>
													{formatDuration(trace.duration_ms)}
												</td>
												<td>
													<small>{formatTime(trace.collected_at)}</small>
												</td>
												<td>
													<button class="btn btn-sm btn-outline-info">
														<i class="fas fa-eye"></i>
													</button>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}

		<!-- 性能分析 -->
		{#if activeTab === 'analysis'}
			<div class="tab-content">
				<!-- 分析參數 -->
				<div class="card mb-4">
					<div class="card-body">
						<div class="row">
							<div class="col-md-4">
								<label class="form-label">服務名稱</label>
								<input 
									type="text" 
									class="form-control" 
									placeholder="留空為分析所有服務"
									bind:value={analysisParams.service_name}
								>
							</div>
							<div class="col-md-4">
								<label class="form-label">分析時間範圍</label>
								<select class="form-select" bind:value={analysisParams.hours}>
									<option value={1}>1小時</option>
									<option value={6}>6小時</option>
									<option value={24}>24小時</option>
									<option value={72}>3天</option>
								</select>
							</div>
							<div class="col-md-4">
								<label class="form-label">時間間隔</label>
								<select class="form-select" bind:value={analysisParams.interval_minutes}>
									<option value={15}>15分鐘</option>
									<option value={30}>30分鐘</option>
									<option value={60}>1小時</option>
									<option value={180}>3小時</option>
								</select>
							</div>
						</div>
						<div class="mt-3">
							<button class="btn btn-primary" on:click={fetchAnalysisData}>
								<i class="fas fa-chart-line"></i> 重新分析
							</button>
						</div>
					</div>
				</div>

				<!-- 性能指標 -->
				{#if $analysisData.performance && $analysisData.performance.performance_metrics}
					<div class="row mb-4">
						<div class="col-md-3">
							<div class="card border-primary">
								<div class="card-body text-center">
									<h3 class="text-primary">{$analysisData.performance.total_requests}</h3>
									<small class="text-muted">總請求數</small>
								</div>
							</div>
						</div>
						<div class="col-md-3">
							<div class="card border-success">
								<div class="card-body text-center">
									<h3 class="text-success">{$analysisData.performance.performance_metrics.avg_duration_ms}ms</h3>
									<small class="text-muted">平均響應時間</small>
								</div>
							</div>
						</div>
						<div class="col-md-3">
							<div class="card border-warning">
								<div class="card-body text-center">
									<h3 class="text-warning">{$analysisData.performance.performance_metrics.p95_duration_ms}ms</h3>
									<small class="text-muted">P95 響應時間</small>
								</div>
							</div>
						</div>
						<div class="col-md-3">
							<div class="card border-danger">
								<div class="card-body text-center">
									<h3 class="text-danger">{$analysisData.performance.error_rate}%</h3>
									<small class="text-muted">錯誤率</small>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- 錯誤分析 -->
				{#if $analysisData.errors && $analysisData.errors.total_errors}
					<div class="card mb-4">
						<div class="card-header">
							<h5 class="mb-0">錯誤分析</h5>
						</div>
						<div class="card-body">
							<div class="row">
								<div class="col-md-6">
									<h6>錯誤類型分佈</h6>
									<div class="table-responsive">
										<table class="table table-sm">
											<thead>
												<tr>
													<th>錯誤類型</th>
													<th>次數</th>
												</tr>
											</thead>
											<tbody>
												{#each Object.entries($analysisData.errors.error_types) as [type, count]}
													<tr>
														<td>{type}</td>
														<td><span class="badge bg-danger">{count}</span></td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
								<div class="col-md-6">
									<h6>受影響服務</h6>
									<div class="table-responsive">
										<table class="table table-sm">
											<thead>
												<tr>
													<th>服務</th>
													<th>錯誤數</th>
												</tr>
											</thead>
											<tbody>
												{#each Object.entries($analysisData.errors.error_services) as [service, count]}
													<tr>
														<td>{service}</td>
														<td><span class="badge bg-warning">{count}</span></td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- 服務分析 -->
				{#if $analysisData.services && $analysisData.services.services}
					<div class="card">
						<div class="card-header">
							<h5 class="mb-0">服務性能分析</h5>
						</div>
						<div class="card-body">
							<div class="table-responsive">
								<table class="table table-hover">
									<thead>
										<tr>
											<th>服務名稱</th>
											<th>請求數</th>
											<th>錯誤率</th>
											<th>平均響應時間</th>
											<th>操作數</th>
											<th>依賴數</th>
										</tr>
									</thead>
									<tbody>
										{#each Object.entries($analysisData.services.services) as [serviceName, serviceData]}
											<tr>
												<td><strong>{serviceName}</strong></td>
												<td>{serviceData.request_count}</td>
												<td>
													<span class="badge bg-{serviceData.error_rate > 5 ? 'danger' : serviceData.error_rate > 1 ? 'warning' : 'success'}">
														{serviceData.error_rate}%
													</span>
												</td>
												<td>{serviceData.avg_duration_ms}ms</td>
												<td>{serviceData.operation_count}</td>
												<td>{serviceData.dependencies.length}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- 系統健康 -->
		{#if activeTab === 'health'}
			<div class="tab-content">
				<!-- 整體健康狀態 -->
				{#if $healthData.overall && $healthData.overall.health_score !== undefined}
					<div class="card mb-4">
						<div class="card-header">
							<h5 class="mb-0">系統健康狀態</h5>
						</div>
						<div class="card-body text-center">
							<div class="row">
								<div class="col-md-4">
									<h2 class="text-{getHealthColor($healthData.overall.status)}">
										{$healthData.overall.health_score}
									</h2>
									<p class="text-muted">健康評分</p>
									<span class="badge bg-{getHealthColor($healthData.overall.status)} fs-6">
										{$healthData.overall.status.toUpperCase()}
									</span>
								</div>
								<div class="col-md-4">
									<h3>{$healthData.overall.details?.error_rate || 0}%</h3>
									<p class="text-muted">錯誤率</p>
								</div>
								<div class="col-md-4">
									<h3>{$healthData.overall.details?.avg_duration_ms || 0}ms</h3>
									<p class="text-muted">平均響應時間</p>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- 慢操作 -->
				{#if $healthData.slowOperations && $healthData.slowOperations.length > 0}
					<div class="card mb-4">
						<div class="card-header">
							<h5 class="mb-0">最慢的操作</h5>
						</div>
						<div class="card-body">
							<div class="table-responsive">
								<table class="table table-hover">
									<thead>
										<tr>
											<th>服務</th>
											<th>操作</th>
											<th>平均時間</th>
											<th>P95 時間</th>
											<th>請求數</th>
											<th>錯誤率</th>
										</tr>
									</thead>
									<tbody>
										{#each $healthData.slowOperations as op}
											<tr>
												<td>{op.service_name}</td>
												<td>{op.operation_name}</td>
												<td>
													<span class="badge bg-{op.avg_duration_ms > 1000 ? 'danger' : op.avg_duration_ms > 500 ? 'warning' : 'success'}">
														{op.avg_duration_ms}ms
													</span>
												</td>
												<td>{op.p95_duration_ms}ms</td>
												<td>{op.total_requests}</td>
												<td>
													<span class="badge bg-{op.error_rate > 5 ? 'danger' : op.error_rate > 1 ? 'warning' : 'success'}">
														{op.error_rate}%
													</span>
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					</div>
				{/if}

				<!-- 收集器統計 -->
				{#if $healthData.collectorStats}
					<div class="card">
						<div class="card-header">
							<h5 class="mb-0">追蹤收集器狀態</h5>
						</div>
						<div class="card-body">
							<div class="row">
								<div class="col-md-3">
									<div class="card border-info">
										<div class="card-body text-center">
											<h4 class="text-info">{$healthData.collectorStats.total_traces || 0}</h4>
											<small class="text-muted">總追蹤數</small>
										</div>
									</div>
								</div>
								<div class="col-md-3">
									<div class="card border-success">
										<div class="card-body text-center">
											<h4 class="text-success">{$healthData.collectorStats.total_spans || 0}</h4>
											<small class="text-muted">總 Span 數</small>
										</div>
									</div>
								</div>
								<div class="col-md-3">
									<div class="card border-warning">
										<div class="card-body text-center">
											<h4 class="text-warning">{$healthData.collectorStats.memory_traces_count || 0}</h4>
											<small class="text-muted">內存追蹤數</small>
										</div>
									</div>
								</div>
								<div class="col-md-3">
									<div class="card border-danger">
										<div class="card-body text-center">
											<h4 class="text-danger">{$healthData.collectorStats.error_traces || 0}</h4>
											<small class="text-muted">錯誤追蹤數</small>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<!-- 搜索模態框 -->
{#if showSearchModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">搜索追蹤</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showSearchModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="mb-3">
						<label class="form-label">搜索關鍵字</label>
						<input 
							type="text" 
							class="form-control" 
							placeholder="輸入追蹤ID、操作名稱或錯誤信息..."
							bind:value={searchQuery}
						>
					</div>
					<div class="mb-3">
						<label class="form-label">服務名稱</label>
						<input 
							type="text" 
							class="form-control" 
							placeholder="可選：限制搜索範圍"
							bind:value={searchParams.service_name}
						>
					</div>
					<div class="mb-3">
						<label class="form-label">搜索時間範圍</label>
						<select class="form-select" bind:value={searchParams.hours}>
							<option value={1}>1小時</option>
							<option value={6}>6小時</option>
							<option value={24}>24小時</option>
							<option value={72}>3天</option>
						</select>
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showSearchModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-primary" 
						on:click={searchTraces}
					>
						<i class="fas fa-search"></i> 搜索
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<!-- 導出模態框 -->
{#if showExportModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">導出追蹤資料</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showExportModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="mb-3">
						<label class="form-label">開始日期</label>
						<input 
							type="date" 
							class="form-control" 
							bind:value={exportParams.start_date}
						>
					</div>
					<div class="mb-3">
						<label class="form-label">結束日期</label>
						<input 
							type="date" 
							class="form-control" 
							bind:value={exportParams.end_date}
						>
					</div>
					<div class="alert alert-info">
						<i class="fas fa-info-circle"></i>
						留空日期將導出所有可用的追蹤資料
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showExportModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-success" 
						on:click={exportTraces}
					>
						<i class="fas fa-download"></i> 導出
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<style>
	.tracing-dashboard {
		padding: 1rem;
	}

	.card {
		box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
	}

	.nav-tabs .nav-link {
		border: none;
		background: none;
		color: #6c757d;
		padding: 0.75rem 1rem;
	}

	.nav-tabs .nav-link.active {
		background-color: #fff;
		border-bottom: 2px solid #0d6efd;
		color: #0d6efd;
		font-weight: 600;
	}

	.nav-tabs .nav-link:hover {
		background-color: #f8f9fa;
		color: #0d6efd;
	}

	.modal {
		background: rgba(0, 0, 0, 0.5);
	}

	.table th {
		border-top: none;
		font-weight: 600;
	}

	code {
		font-size: 0.875em;
	}
</style>
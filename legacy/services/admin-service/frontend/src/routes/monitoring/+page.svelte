<script>
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	// 狀態管理
	let healthStatus = writable({});
	let alerts = writable([]);
	let metrics = writable({});
	let thresholds = writable({});
	let loading = writable(true);
	let autoRefresh = writable(true);
	let refreshInterval = null;

	// API 基礎 URL
	const API_BASE = '/admin/monitoring';

	// 獲取健康狀態
	async function fetchHealthStatus() {
		try {
			const response = await fetch(`${API_BASE}/health`);
			const data = await response.json();
			if (data.success) {
				healthStatus.set(data.data);
			}
		} catch (error) {
			console.error('獲取健康狀態失敗:', error);
		}
	}

	// 獲取活躍告警
	async function fetchAlerts() {
		try {
			const response = await fetch(`${API_BASE}/alerts`);
			const data = await response.json();
			if (data.success) {
				alerts.set(data.data);
			}
		} catch (error) {
			console.error('獲取告警失敗:', error);
		}
	}

	// 獲取指標摘要
	async function fetchMetricsSummary() {
		try {
			const response = await fetch(`${API_BASE}/metrics/summary`);
			const data = await response.json();
			if (data.success) {
				metrics.set(data.data);
			}
		} catch (error) {
			console.error('獲取指標摘要失敗:', error);
		}
	}

	// 獲取閾值配置
	async function fetchThresholds() {
		try {
			const response = await fetch(`${API_BASE}/config/thresholds`);
			const data = await response.json();
			if (data.success) {
				thresholds.set(data.data);
			}
		} catch (error) {
			console.error('獲取閾值配置失敗:', error);
		}
	}

	// 手動觸發健康檢查
	async function triggerHealthCheck() {
		try {
			const response = await fetch(`${API_BASE}/health/check`, {
				method: 'POST'
			});
			const data = await response.json();
			if (data.success) {
				alert('健康檢查已觸發');
				await fetchAllData();
			} else {
				alert('觸發健康檢查失敗: ' + data.message);
			}
		} catch (error) {
			console.error('觸發健康檢查失敗:', error);
			alert('觸發健康檢查失敗');
		}
	}

	// 啟動監控
	async function startMonitoring() {
		try {
			const response = await fetch(`${API_BASE}/start`, {
				method: 'POST'
			});
			const data = await response.json();
			if (data.success) {
				alert('監控已啟動');
			} else {
				alert('啟動監控失敗: ' + data.message);
			}
		} catch (error) {
			console.error('啟動監控失敗:', error);
			alert('啟動監控失敗');
		}
	}

	// 停止監控
	async function stopMonitoring() {
		try {
			const response = await fetch(`${API_BASE}/stop`, {
				method: 'POST'
			});
			const data = await response.json();
			if (data.success) {
				alert('監控已停止');
			} else {
				alert('停止監控失敗: ' + data.message);
			}
		} catch (error) {
			console.error('停止監控失敗:', error);
			alert('停止監控失敗');
		}
	}

	// 獲取所有數據
	async function fetchAllData() {
		loading.set(true);
		await Promise.all([
			fetchHealthStatus(),
			fetchAlerts(),
			fetchMetricsSummary(),
			fetchThresholds()
		]);
		loading.set(false);
	}

	// 格式化時間
	function formatTime(timestamp) {
		if (!timestamp) return '未知';
		return new Date(timestamp).toLocaleString('zh-TW');
	}

	// 獲取狀態顏色
	function getStatusColor(status) {
		switch (status) {
			case 'healthy': return 'success';
			case 'warning': return 'warning';
			case 'critical': return 'danger';
			default: return 'secondary';
		}
	}

	// 獲取告警級別顏色
	function getAlertColor(level) {
		switch (level) {
			case 'info': return 'info';
			case 'warning': return 'warning';
			case 'error': return 'danger';
			case 'critical': return 'dark';
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
	<title>系統監控 - 後台管理</title>
</svelte:head>

<div class="monitoring-dashboard">
	<div class="d-flex justify-content-between align-items-center mb-4">
		<h1>系統監控</h1>
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
			<button class="btn btn-primary" on:click={triggerHealthCheck}>
				<i class="fas fa-heartbeat"></i> 檢查健康
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
		<!-- 整體狀態卡片 -->
		<div class="row mb-4">
			<div class="col-12">
				<div class="card border-{getStatusColor($metrics.overall_status)}">
					<div class="card-header bg-{getStatusColor($metrics.overall_status)} text-white">
						<h5 class="mb-0">
							<i class="fas fa-shield-alt"></i> 
							系統整體狀態: {$metrics.overall_status || '未知'}
						</h5>
					</div>
					<div class="card-body">
						<div class="row">
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-success">{$metrics.healthy_components || 0}</h3>
									<small class="text-muted">健康組件</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-warning">{$metrics.warning_components || 0}</h3>
									<small class="text-muted">警告組件</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-danger">{$metrics.critical_components || 0}</h3>
									<small class="text-muted">嚴重組件</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-info">{$metrics.active_alerts || 0}</h3>
									<small class="text-muted">活躍告警</small>
								</div>
							</div>
						</div>
						<hr>
						<small class="text-muted">
							最後檢查: {formatTime($metrics.last_check)}
						</small>
					</div>
				</div>
			</div>
		</div>

		<!-- 組件狀態 -->
		{#if $healthStatus.components}
			<div class="row mb-4">
				<div class="col-12">
					<div class="card">
						<div class="card-header">
							<h5 class="mb-0">
								<i class="fas fa-cubes"></i> 組件狀態
							</h5>
						</div>
						<div class="card-body">
							<div class="row">
								{#each Object.entries($healthStatus.components) as [componentName, component]}
									<div class="col-lg-4 col-md-6 mb-3">
										<div class="card border-{getStatusColor(component.status)}">
											<div class="card-header bg-{getStatusColor(component.status)} text-white">
												<h6 class="mb-0">{componentName}</h6>
											</div>
											<div class="card-body">
												<p class="mb-2">{component.message}</p>
												<small class="text-muted">
													執行時間: {component.execution_time_ms}ms
												</small>
												
												{#if component.metrics && component.metrics.length > 0}
													<hr>
													<div class="metrics">
														{#each component.metrics as metric}
															<div class="d-flex justify-content-between">
																<span class="text-muted">{metric.description || metric.name}:</span>
																<span class="fw-bold">
																	{metric.value}{metric.unit || ''}
																</span>
															</div>
														{/each}
													</div>
												{/if}
											</div>
										</div>
									</div>
								{/each}
							</div>
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- 活躍告警 -->
		{#if $alerts.length > 0}
			<div class="row mb-4">
				<div class="col-12">
					<div class="card">
						<div class="card-header">
							<h5 class="mb-0">
								<i class="fas fa-exclamation-triangle"></i> 
								活躍告警 ({$alerts.length})
							</h5>
						</div>
						<div class="card-body">
							{#each $alerts as alert}
								<div class="alert alert-{getAlertColor(alert.level)} mb-2">
									<div class="d-flex justify-content-between align-items-start">
										<div>
											<h6 class="alert-heading mb-1">{alert.title}</h6>
											<p class="mb-1">{alert.message}</p>
											<small class="text-muted">
												組件: {alert.component} | 
												時間: {formatTime(alert.timestamp)}
											</small>
										</div>
										<span class="badge bg-{getAlertColor(alert.level)}">{alert.level}</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- 監控配置 -->
		<div class="row">
			<div class="col-12">
				<div class="card">
					<div class="card-header">
						<h5 class="mb-0">
							<i class="fas fa-cog"></i> 監控配置
						</h5>
					</div>
					<div class="card-body">
						<div class="row mb-3">
							<div class="col-md-6">
								<button class="btn btn-success me-2" on:click={startMonitoring}>
									<i class="fas fa-play"></i> 啟動監控
								</button>
								<button class="btn btn-danger" on:click={stopMonitoring}>
									<i class="fas fa-stop"></i> 停止監控
								</button>
							</div>
						</div>

						{#if Object.keys($thresholds).length > 0}
							<h6>監控閾值</h6>
							<div class="table-responsive">
								<table class="table table-sm">
									<thead>
										<tr>
											<th>指標</th>
											<th>警告閾值</th>
											<th>嚴重閾值</th>
										</tr>
									</thead>
									<tbody>
										{#each Object.entries($thresholds) as [metric, values]}
											<tr>
												<td>{metric}</td>
												<td class="text-warning">{values.warning}</td>
												<td class="text-danger">{values.critical}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.monitoring-dashboard {
		padding: 1rem;
	}

	.metrics {
		font-size: 0.9rem;
	}

	.card {
		box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
	}

	.card-header {
		font-weight: 600;
	}

	.alert {
		border-left: 4px solid currentColor;
	}

	.spinner-border {
		width: 3rem;
		height: 3rem;
	}
</style>
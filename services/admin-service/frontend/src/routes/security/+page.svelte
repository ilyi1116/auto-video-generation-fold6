<script>
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	// 狀態管理
	let rateLimitStats = writable({});
	let threatAnalysis = writable({});
	let blacklist = writable([]);
	let loading = writable(true);
	let autoRefresh = writable(true);
	let refreshInterval = null;

	// 表單狀態
	let newIpAddress = '';
	let blacklistDuration = 24;
	let showAddIpModal = false;

	// API 基礎 URL
	const API_BASE = '/admin/security';

	// 獲取限流統計
	async function fetchRateLimitStats() {
		try {
			const response = await fetch(`${API_BASE}/rate-limits/stats`);
			const data = await response.json();
			if (data.success) {
				rateLimitStats.set(data.data);
			}
		} catch (error) {
			console.error('獲取限流統計失敗:', error);
		}
	}

	// 獲取威脅分析
	async function fetchThreatAnalysis() {
		try {
			const response = await fetch(`${API_BASE}/threats/analysis?hours=24`);
			const data = await response.json();
			if (data.success) {
				threatAnalysis.set(data.data);
			}
		} catch (error) {
			console.error('獲取威脅分析失敗:', error);
		}
	}

	// 獲取黑名單
	async function fetchBlacklist() {
		try {
			const response = await fetch(`${API_BASE}/blacklist`);
			const data = await response.json();
			if (data.success) {
				blacklist.set(data.data.blacklist);
			}
		} catch (error) {
			console.error('獲取黑名單失敗:', error);
		}
	}

	// 添加 IP 到黑名單
	async function addToBlacklist() {
		if (!newIpAddress) {
			alert('請輸入 IP 地址');
			return;
		}

		try {
			const response = await fetch(`${API_BASE}/blacklist`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					ip_address: newIpAddress,
					duration_hours: blacklistDuration
				})
			});
			
			const data = await response.json();
			if (data.success) {
				alert('IP 已添加到黑名單');
				newIpAddress = '';
				blacklistDuration = 24;
				showAddIpModal = false;
				await fetchBlacklist();
			} else {
				alert('添加失敗: ' + data.message);
			}
		} catch (error) {
			console.error('添加黑名單失敗:', error);
			alert('添加失敗');
		}
	}

	// 從黑名單移除 IP
	async function removeFromBlacklist(ip) {
		if (!confirm(`確定要從黑名單移除 IP ${ip} 嗎？`)) {
			return;
		}

		try {
			const response = await fetch(`${API_BASE}/blacklist/${encodeURIComponent(ip)}`, {
				method: 'DELETE'
			});
			
			const data = await response.json();
			if (data.success) {
				alert('IP 已從黑名單移除');
				await fetchBlacklist();
			} else {
				alert('移除失敗: ' + data.message);
			}
		} catch (error) {
			console.error('移除黑名單失敗:', error);
			alert('移除失敗');
		}
	}

	// 測試限流
	async function testRateLimit() {
		try {
			const response = await fetch(`${API_BASE}/test-rate-limit`, {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.success) {
				alert(`限流測試結果: ${data.message}`);
			} else {
				alert(`限流測試: ${data.message}`);
			}
		} catch (error) {
			console.error('測試限流失敗:', error);
			alert('測試失敗');
		}
	}

	// 獲取所有數據
	async function fetchAllData() {
		loading.set(true);
		await Promise.all([
			fetchRateLimitStats(),
			fetchThreatAnalysis(),
			fetchBlacklist()
		]);
		loading.set(false);
	}

	// 格式化時間
	function formatTime(timestamp) {
		if (!timestamp) return '未知';
		return new Date(timestamp).toLocaleString('zh-TW');
	}

	// 獲取威脅等級顏色
	function getThreatLevelColor(level) {
		switch (level) {
			case 'minimal': return 'success';
			case 'low': return 'info';
			case 'medium': return 'warning';
			case 'high': return 'danger';
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
	<title>API 安全防護 - 後台管理</title>
</svelte:head>

<div class="security-dashboard">
	<div class="d-flex justify-content-between align-items-center mb-4">
		<h1>API 安全防護</h1>
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
			<button class="btn btn-info" on:click={testRateLimit}>
				<i class="fas fa-vial"></i> 測試限流
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
		<!-- 威脅分析摘要 -->
		<div class="row mb-4">
			<div class="col-12">
				<div class="card border-{getThreatLevelColor($threatAnalysis.threat_level)}">
					<div class="card-header bg-{getThreatLevelColor($threatAnalysis.threat_level)} text-white">
						<h5 class="mb-0">
							<i class="fas fa-shield-alt"></i> 
							威脅等級: {$threatAnalysis.threat_level || '未知'}
						</h5>
					</div>
					<div class="card-body">
						<div class="row">
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-danger">{$threatAnalysis.total_threats || 0}</h3>
									<small class="text-muted">總威脅數</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-warning">{$threatAnalysis.rate_limit_violations || 0}</h3>
									<small class="text-muted">限流違規</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-info">{$threatAnalysis.invalid_tokens || 0}</h3>
									<small class="text-muted">無效令牌</small>
								</div>
							</div>
							<div class="col-md-3">
								<div class="text-center">
									<h3 class="text-secondary">{$threatAnalysis.unique_ips || 0}</h3>
									<small class="text-muted">唯一 IP</small>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 限流統計 -->
		<div class="row mb-4">
			<div class="col-lg-6">
				<div class="card">
					<div class="card-header">
						<h5 class="mb-0">
							<i class="fas fa-tachometer-alt"></i> 限流配置統計
						</h5>
					</div>
					<div class="card-body">
						{#if $rateLimitStats.default_limits}
							<div class="row">
								<div class="col-md-6">
									<div class="text-center mb-3">
										<h4 class="text-primary">{Object.keys($rateLimitStats.default_limits).length}</h4>
										<small class="text-muted">默認限制規則</small>
									</div>
								</div>
								<div class="col-md-6">
									<div class="text-center mb-3">
										<h4 class="text-info">{Object.keys($rateLimitStats.endpoint_limits).length}</h4>
										<small class="text-muted">端點特定規則</small>
									</div>
								</div>
							</div>
							
							<div class="row">
								<div class="col-md-6">
									<div class="text-center">
										<h4 class="text-success">{$rateLimitStats.whitelist_count || 0}</h4>
										<small class="text-muted">白名單 IP</small>
									</div>
								</div>
								<div class="col-md-6">
									<div class="text-center">
										<h4 class="text-danger">{$rateLimitStats.blacklist_count || 0}</h4>
										<small class="text-muted">黑名單 IP</small>
									</div>
								</div>
							</div>
						{/if}
						
						<hr>
						<div class="d-flex justify-content-between align-items-center">
							<span class="text-muted">Redis 狀態:</span>
							<span class="badge bg-{$rateLimitStats.redis_connected ? 'success' : 'warning'}">
								{$rateLimitStats.redis_connected ? '已連接' : '未連接'}
							</span>
						</div>
					</div>
				</div>
			</div>

			<div class="col-lg-6">
				<div class="card">
					<div class="card-header d-flex justify-content-between align-items-center">
						<h5 class="mb-0">
							<i class="fas fa-ban"></i> 黑名單管理
						</h5>
						<button class="btn btn-sm btn-danger" on:click={() => showAddIpModal = true}>
							<i class="fas fa-plus"></i> 添加 IP
						</button>
					</div>
					<div class="card-body">
						{#if $blacklist.length === 0}
							<p class="text-muted text-center">暫無黑名單 IP</p>
						{:else}
							<div class="list-group">
								{#each $blacklist as ip}
									<div class="list-group-item d-flex justify-content-between align-items-center">
										<span class="font-monospace">{ip}</span>
										<button 
											class="btn btn-sm btn-outline-danger"
											on:click={() => removeFromBlacklist(ip)}
										>
											<i class="fas fa-times"></i>
										</button>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- 高風險 IP -->
		{#if $threatAnalysis.top_threat_ips && $threatAnalysis.top_threat_ips.length > 0}
			<div class="row">
				<div class="col-12">
					<div class="card">
						<div class="card-header">
							<h5 class="mb-0">
								<i class="fas fa-exclamation-triangle"></i> 高風險 IP (24小時)
							</h5>
						</div>
						<div class="card-body">
							<div class="table-responsive">
								<table class="table table-striped">
									<thead>
										<tr>
											<th>IP 地址</th>
											<th>威脅次數</th>
											<th>操作</th>
										</tr>
									</thead>
									<tbody>
										{#each $threatAnalysis.top_threat_ips as item}
											<tr>
												<td class="font-monospace">{item.ip}</td>
												<td>
													<span class="badge bg-danger">{item.count}</span>
												</td>
												<td>
													<button 
														class="btn btn-sm btn-danger"
														on:click={() => {
															newIpAddress = item.ip;
															showAddIpModal = true;
														}}
													>
														<i class="fas fa-ban"></i> 加入黑名單
													</button>
												</td>
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
	{/if}
</div>

<!-- 添加 IP 到黑名單的模態框 -->
{#if showAddIpModal}
	<div class="modal fade show d-block" tabindex="-1">
		<div class="modal-dialog">
			<div class="modal-content">
				<div class="modal-header">
					<h5 class="modal-title">添加 IP 到黑名單</h5>
					<button 
						type="button" 
						class="btn-close" 
						on:click={() => showAddIpModal = false}
					></button>
				</div>
				<div class="modal-body">
					<div class="mb-3">
						<label for="ipAddress" class="form-label">IP 地址</label>
						<input 
							type="text" 
							class="form-control" 
							id="ipAddress"
							bind:value={newIpAddress}
							placeholder="例如: 192.168.1.100"
						>
					</div>
					<div class="mb-3">
						<label for="duration" class="form-label">封禁時長 (小時)</label>
						<input 
							type="number" 
							class="form-control" 
							id="duration"
							bind:value={blacklistDuration}
							min="1"
							max="8760"
						>
					</div>
				</div>
				<div class="modal-footer">
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showAddIpModal = false}
					>
						取消
					</button>
					<button 
						type="button" 
						class="btn btn-danger" 
						on:click={addToBlacklist}
					>
						<i class="fas fa-ban"></i> 添加黑名單
					</button>
				</div>
			</div>
		</div>
	</div>
	<div class="modal-backdrop fade show"></div>
{/if}

<style>
	.security-dashboard {
		padding: 1rem;
	}

	.card {
		box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
	}

	.card-header {
		font-weight: 600;
	}

	.font-monospace {
		font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
	}

	.spinner-border {
		width: 3rem;
		height: 3rem;
	}

	.modal {
		background: rgba(0, 0, 0, 0.5);
	}
</style>
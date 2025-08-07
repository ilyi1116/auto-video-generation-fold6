<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.js';

	let isAdmin = false;

	onMount(() => {
		// 檢查用戶是否為管理員
		authStore.subscribe(auth => {
			if (auth.user) {
				isAdmin = auth.user.role === 'ADMIN';
				if (!isAdmin) {
					// 非管理員重導向到主頁
					goto('/');
				}
			} else {
				// 未登入重導向到登入頁
				goto('/login');
			}
		});
	});

	const sidebarItems = [
		{ name: '儀表板', href: '/admin', icon: '📊' },
		{ name: '假資料管理', href: '/admin/mock-data', icon: '🗃️' },
		{ name: '用戶管理', href: '/admin/users', icon: '👥' },
		{ name: '內容管理', href: '/admin/content', icon: '🎬' },
		{ name: '系統設定', href: '/admin/settings', icon: '⚙️' },
		{ name: '日誌查看', href: '/admin/logs', icon: '📝' }
	];
</script>

<div class="min-h-screen bg-gray-50 flex">
	<!-- 側邊欄 -->
	<div class="w-64 bg-white shadow-sm border-r border-gray-200">
		<div class="p-6 border-b border-gray-200">
			<h1 class="text-xl font-bold text-gray-900">管理後台</h1>
			<p class="text-sm text-gray-600">Auto Video Platform</p>
		</div>
		
		<nav class="p-4">
			{#each sidebarItems as item}
				<a
					href={item.href}
					class="flex items-center px-4 py-3 mb-2 text-sm rounded-lg transition-colors {
						$page.url.pathname === item.href 
						? 'bg-blue-50 text-blue-700 border-l-4 border-blue-700' 
						: 'text-gray-700 hover:bg-gray-100'
					}"
				>
					<span class="mr-3 text-lg">{item.icon}</span>
					{item.name}
				</a>
			{/each}
		</nav>

		<!-- 用戶資訊 -->
		<div class="absolute bottom-0 left-0 right-0 w-64 p-4 border-t border-gray-200">
			{#if $authStore.user}
				<div class="flex items-center">
					<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
						<span class="text-white text-sm font-medium">
							{$authStore.user.full_name?.charAt(0) || 'A'}
						</span>
					</div>
					<div class="ml-3">
						<p class="text-sm font-medium text-gray-900">{$authStore.user.full_name}</p>
						<p class="text-xs text-gray-500">{$authStore.user.email}</p>
					</div>
				</div>
				
				<button 
					on:click={() => authStore.logout()}
					class="mt-3 w-full text-left text-sm text-gray-500 hover:text-gray-700"
				>
					登出
				</button>
			{/if}
		</div>
	</div>

	<!-- 主要內容區域 -->
	<div class="flex-1 flex flex-col">
		<!-- 頂部導航欄 -->
		<header class="bg-white shadow-sm border-b border-gray-200">
			<div class="px-6 py-4 flex items-center justify-between">
				<div>
					<h2 class="text-lg font-semibold text-gray-900">
						{#if $page.url.pathname === '/admin'}
							儀表板概覽
						{:else if $page.url.pathname === '/admin/mock-data'}
							假資料管理
						{:else if $page.url.pathname === '/admin/users'}
							用戶管理
						{:else if $page.url.pathname === '/admin/content'}
							內容管理
						{:else if $page.url.pathname === '/admin/settings'}
							系統設定
						{:else if $page.url.pathname === '/admin/logs'}
							系統日誌
						{:else}
							管理後台
						{/if}
					</h2>
					<p class="text-sm text-gray-600">
						{new Date().toLocaleDateString('zh-TW', { 
							year: 'numeric', 
							month: 'long', 
							day: 'numeric',
							weekday: 'long'
						})}
					</p>
				</div>
				
				<div class="flex items-center space-x-4">
					<!-- 通知按鈕 -->
					<button class="relative p-2 text-gray-400 hover:text-gray-600">
						<span class="text-lg">🔔</span>
						<!-- 通知點 -->
						<span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
					</button>
					
					<!-- 返回前台 -->
					<a 
						href="/"
						class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
					>
						返回前台
					</a>
				</div>
			</div>
		</header>

		<!-- 頁面內容 -->
		<main class="flex-1 p-6 overflow-auto">
			{#if isAdmin}
				<slot />
			{:else}
				<div class="flex items-center justify-center h-64">
					<div class="text-center">
						<div class="text-4xl mb-4">🔒</div>
						<h3 class="text-lg font-medium text-gray-900">權限不足</h3>
						<p class="text-gray-600">需要管理員權限才能訪問此頁面</p>
					</div>
				</div>
			{/if}
		</main>
	</div>
</div>

<style>
	/* 確保側邊欄在小螢幕上也能正常顯示 */
	@media (max-width: 768px) {
		.w-64 {
			width: 100%;
			position: fixed;
			top: 0;
			left: 0;
			z-index: 50;
			transform: translateX(-100%);
			transition: transform 0.3s ease-in-out;
		}
		
		.w-64.open {
			transform: translateX(0);
		}
	}
</style>
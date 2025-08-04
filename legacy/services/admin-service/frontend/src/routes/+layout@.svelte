<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { authStore, authActions } from '$stores/auth';
	import { goto } from '$app/navigation';
	import toast, { Toaster } from 'svelte-french-toast';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';

	let mounted = false;
	let sidebarOpen = false; // 手機版預設關閉

	onMount(() => {
		// 初始化認證狀態
		authActions.initFromStorage();
		mounted = true;
	});

	// 監聽認證狀態變化，重定向到登錄頁面
	$: if (mounted && !$authStore.isAuthenticated && $page.route.id !== '/login') {
		goto('/login');
	}

	// 如果已登錄且在登錄頁面，重定向到首頁
	$: if (mounted && $authStore.isAuthenticated && $page.route.id === '/login') {
		goto('/');
	}

	// 切換側邊欄
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	// 點擊遮罩層關閉側邊欄
	function closeSidebar() {
		sidebarOpen = false;
	}

	// 是否顯示完整佈局（非登錄頁面）
	$: showLayout = mounted && $authStore.isAuthenticated && $page.route.id !== '/login';
</script>

<svelte:head>
	<title>後台管理系統</title>
</svelte:head>

<!-- Toast 通知組件 -->
<Toaster
	position="top-right"
	toastOptions={{
		duration: 4000,
		style: 'border-radius: 8px; background: #333; color: #fff;'
	}}
/>

{#if showLayout}
	<!-- 完整佈局 -->
	<div class="h-screen flex overflow-hidden bg-gray-100">
		<!-- 側邊欄 -->
		<Sidebar bind:sidebarOpen />

		<!-- 手機版遮罩層 -->
		{#if sidebarOpen}
			<div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden" on:click={closeSidebar}></div>
		{/if}

		<!-- 主要內容區域 -->
		<div class="flex flex-col w-0 flex-1 overflow-hidden">
			<!-- 頂部導航 -->
			<Header bind:sidebarOpen {toggleSidebar} />

			<!-- 主要內容 -->
			<main class="flex-1 relative overflow-y-auto focus:outline-none">
				<div class="py-6">
					<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
						<slot />
					</div>
				</div>
			</main>
		</div>
	</div>
{:else}
	<!-- 登錄頁面或載入中 -->
	<main class="min-h-screen bg-gray-50">
		<slot />
	</main>
{/if}
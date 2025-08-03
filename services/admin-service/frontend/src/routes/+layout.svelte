<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { authStore, authActions } from '$stores/auth';
	import { goto } from '$app/navigation';
	import toast, { Toaster } from 'svelte-french-toast';

	let mounted = false;

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

<main class="min-h-screen bg-gray-50">
	<slot />
</main>
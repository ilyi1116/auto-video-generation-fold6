<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore, authActions } from '$stores/auth';
	import { apiClient } from '$utils/api';
	import toast from 'svelte-french-toast';
	import { Eye, EyeOff, Shield, Lock, User } from 'lucide-svelte';

	let username = '';
	let password = '';
	let showPassword = false;
	let loading = false;
	let rememberMe = false;

	// 如果已經登錄，重定向到首頁
	onMount(() => {
		if ($authStore.isAuthenticated) {
			goto('/');
		}
	});

	async function handleLogin() {
		if (!username || !password) {
			toast.error('請輸入用戶名和密碼');
			return;
		}

		loading = true;
		authActions.setLoading(true);

		try {
			const response = await apiClient.auth.login(username, password);
			const { access_token, user } = response.data;

			// 登錄成功
			authActions.login(access_token, user);
			toast.success(`歡迎回來，${user.full_name || user.username}！`);
			
			// 重定向到首頁
			goto('/');
		} catch (error: any) {
			console.error('登錄失敗:', error);
			
			if (error.response?.status === 401) {
				toast.error('用戶名或密碼錯誤');
			} else if (error.response?.status === 403) {
				toast.error('賬號已被禁用');
			} else {
				toast.error('登錄失敗，請稍後重試');
			}
		} finally {
			loading = false;
			authActions.setLoading(false);
		}
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleLogin();
		}
	}
</script>

<svelte:head>
	<title>登錄 - 後台管理系統</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<!-- 頭部 -->
		<div>
			<div class="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-primary-100">
				<Shield class="h-10 w-10 text-primary-600" />
			</div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
				後台管理系統
			</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				請登錄您的管理員賬號
			</p>
		</div>

		<!-- 登錄表單 -->
		<form class="mt-8 space-y-6" on:submit|preventDefault={handleLogin}>
			<div class="rounded-md shadow-sm -space-y-px">
				<!-- 用戶名 -->
				<div>
					<label for="username" class="sr-only">用戶名</label>
					<div class="relative">
						<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
							<User class="h-5 w-5 text-gray-400" />
						</div>
						<input
							id="username"
							name="username"
							type="text"
							required
							class="appearance-none rounded-none relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
							placeholder="用戶名"
							bind:value={username}
							on:keypress={handleKeyPress}
							disabled={loading}
						/>
					</div>
				</div>

				<!-- 密碼 -->
				<div>
					<label for="password" class="sr-only">密碼</label>
					<div class="relative">
						<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
							<Lock class="h-5 w-5 text-gray-400" />
						</div>
						<input
							id="password"
							name="password"
							type={showPassword ? 'text' : 'password'}
							required
							class="appearance-none rounded-none relative block w-full px-3 py-2 pl-10 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
							placeholder="密碼"
							bind:value={password}
							on:keypress={handleKeyPress}
							disabled={loading}
						/>
						<button
							type="button"
							class="absolute inset-y-0 right-0 pr-3 flex items-center"
							on:click={() => showPassword = !showPassword}
							disabled={loading}
						>
							{#if showPassword}
								<EyeOff class="h-5 w-5 text-gray-400 hover:text-gray-600" />
							{:else}
								<Eye class="h-5 w-5 text-gray-400 hover:text-gray-600" />
							{/if}
						</button>
					</div>
				</div>
			</div>

			<!-- 記住我 -->
			<div class="flex items-center justify-between">
				<div class="flex items-center">
					<input
						id="remember-me"
						name="remember-me"
						type="checkbox"
						class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
						bind:checked={rememberMe}
						disabled={loading}
					/>
					<label for="remember-me" class="ml-2 block text-sm text-gray-900">
						記住我
					</label>
				</div>

				<div class="text-sm">
					<a href="#" class="font-medium text-primary-600 hover:text-primary-500">
						忘記密碼？
					</a>
				</div>
			</div>

			<!-- 登錄按鈕 -->
			<div>
				<button
					type="submit"
					class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
					disabled={loading}
				>
					{#if loading}
						<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						登錄中...
					{:else}
						登錄
					{/if}
				</button>
			</div>

			<!-- 測試賬號提示 -->
			<div class="mt-6 border-t border-gray-200 pt-6">
				<div class="bg-blue-50 border border-blue-200 rounded-md p-4">
					<div class="flex">
						<div class="ml-3">
							<h3 class="text-sm font-medium text-blue-800">
								測試賬號
							</h3>
							<div class="mt-2 text-sm text-blue-700">
								<p><strong>用戶名:</strong> admin</p>
								<p><strong>密碼:</strong> admin123</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</form>
	</div>
</div>
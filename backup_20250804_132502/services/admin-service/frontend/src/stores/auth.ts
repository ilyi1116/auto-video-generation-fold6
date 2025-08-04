import { writable } from 'svelte/store';
import type { Writable } from 'svelte/store';

export interface User {
	id: number;
	username: string;
	email: string;
	full_name: string;
	role: string;
	is_active: boolean;
	is_superuser: boolean;
	permissions: string[];
}

export interface AuthState {
	isAuthenticated: boolean;
	user: User | null;
	token: string | null;
	loading: boolean;
}

const initialState: AuthState = {
	isAuthenticated: false,
	user: null,
	token: null,
	loading: false
};

export const authStore: Writable<AuthState> = writable(initialState);

export const authActions = {
	login: (token: string, user: User) => {
		authStore.update(state => ({
			...state,
			isAuthenticated: true,
			user,
			token,
			loading: false
		}));
		// 儲存到 localStorage
		if (typeof window !== 'undefined') {
			localStorage.setItem('admin_token', token);
			localStorage.setItem('admin_user', JSON.stringify(user));
		}
	},

	logout: () => {
		authStore.set(initialState);
		// 清除 localStorage
		if (typeof window !== 'undefined') {
			localStorage.removeItem('admin_token');
			localStorage.removeItem('admin_user');
		}
	},

	setLoading: (loading: boolean) => {
		authStore.update(state => ({ ...state, loading }));
	},

	initFromStorage: () => {
		if (typeof window !== 'undefined') {
			const token = localStorage.getItem('admin_token');
			const userStr = localStorage.getItem('admin_user');
			
			if (token && userStr) {
				try {
					const user = JSON.parse(userStr);
					authStore.update(state => ({
						...state,
						isAuthenticated: true,
						user,
						token
					}));
				} catch (e) {
					// 清除無效的儲存數據
					localStorage.removeItem('admin_token');
					localStorage.removeItem('admin_user');
				}
			}
		}
	}
};
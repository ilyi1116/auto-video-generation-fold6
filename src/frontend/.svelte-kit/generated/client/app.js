export { matchers } from './matchers.js';

export const nodes = [
	() => import('./nodes/0'),
	() => import('./nodes/1'),
	() => import('./nodes/2'),
	() => import('./nodes/3'),
	() => import('./nodes/4'),
	() => import('./nodes/5'),
	() => import('./nodes/6'),
	() => import('./nodes/7'),
	() => import('./nodes/8'),
	() => import('./nodes/9'),
	() => import('./nodes/10'),
	() => import('./nodes/11'),
	() => import('./nodes/12'),
	() => import('./nodes/13'),
	() => import('./nodes/14'),
	() => import('./nodes/15'),
	() => import('./nodes/16'),
	() => import('./nodes/17'),
	() => import('./nodes/18'),
	() => import('./nodes/19'),
	() => import('./nodes/20'),
	() => import('./nodes/21'),
	() => import('./nodes/22'),
	() => import('./nodes/23'),
	() => import('./nodes/24'),
	() => import('./nodes/25'),
	() => import('./nodes/26'),
	() => import('./nodes/27'),
	() => import('./nodes/28')
];

export const server_loads = [];

export const dictionary = {
		"/": [3],
		"/account/settings": [4],
		"/admin": [5,[2]],
		"/admin/mock-data": [6,[2]],
		"/ai": [7],
		"/ai/images": [8],
		"/ai/music": [9],
		"/ai/script": [10],
		"/ai/voice": [11],
		"/analytics": [12],
		"/assets": [13],
		"/create": [14],
		"/dashboard": [15],
		"/demo": [16],
		"/docs": [17],
		"/forgot-password": [18],
		"/login": [19],
		"/pricing": [20],
		"/profile": [21],
		"/projects": [22],
		"/register": [23],
		"/settings": [24],
		"/social": [25],
		"/trends": [26],
		"/videos": [28],
		"/video/[videoId]": [27]
	};

export const hooks = {
	handleError: (({ error }) => { console.error(error) }),
	
	reroute: (() => {}),
	transport: {}
};

export const decoders = Object.fromEntries(Object.entries(hooks.transport).map(([k, v]) => [k, v.decode]));

export const hash = false;

export const decode = (type, value) => decoders[type](value);

export { default as root } from '../root.svelte';
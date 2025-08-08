type DynamicRoutes = {
	"/video/[videoId]": { videoId: string }
};

type Layouts = {
	"/": { videoId?: string };
	"/account": undefined;
	"/account/settings": undefined;
	"/admin": undefined;
	"/admin/mock-data": undefined;
	"/ai": undefined;
	"/ai/images": undefined;
	"/ai/music": undefined;
	"/ai/script": undefined;
	"/ai/voice": undefined;
	"/analytics": undefined;
	"/assets": undefined;
	"/create": undefined;
	"/dashboard": undefined;
	"/demo": undefined;
	"/forgot-password": undefined;
	"/login": undefined;
	"/pricing": undefined;
	"/profile": undefined;
	"/projects": undefined;
	"/register": undefined;
	"/settings": undefined;
	"/social": undefined;
	"/trends": undefined;
	"/videos": undefined;
	"/video": { videoId?: string };
	"/video/[videoId]": { videoId: string }
};

export type RouteId = "/" | "/account" | "/account/settings" | "/admin" | "/admin/mock-data" | "/ai" | "/ai/images" | "/ai/music" | "/ai/script" | "/ai/voice" | "/analytics" | "/assets" | "/create" | "/dashboard" | "/demo" | "/forgot-password" | "/login" | "/pricing" | "/profile" | "/projects" | "/register" | "/settings" | "/social" | "/trends" | "/videos" | "/video" | "/video/[videoId]";

export type RouteParams<T extends RouteId> = T extends keyof DynamicRoutes ? DynamicRoutes[T] : Record<string, never>;

export type LayoutParams<T extends RouteId> = Layouts[T] | Record<string, never>;

export type Pathname = "/" | "/account" | "/account/settings" | "/admin" | "/admin/mock-data" | "/ai" | "/ai/images" | "/ai/music" | "/ai/script" | "/ai/voice" | "/analytics" | "/assets" | "/create" | "/dashboard" | "/demo" | "/forgot-password" | "/login" | "/pricing" | "/profile" | "/projects" | "/register" | "/settings" | "/social" | "/trends" | "/videos" | "/video" | `/video/${string}` & {};

export type ResolvedPathname = `${"" | `/${string}`}${Pathname}`;

export type Asset = "/manifest.json" | "/service-worker.js";
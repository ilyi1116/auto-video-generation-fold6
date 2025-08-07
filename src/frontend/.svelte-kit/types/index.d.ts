type DynamicRoutes = {
	"/video/[videoId]": { videoId: string }
};

type Layouts = {
	"/": { videoId?: string };
	"/admin": undefined;
	"/admin/mock-data": undefined;
	"/ai": undefined;
	"/ai/images": undefined;
	"/ai/music": undefined;
	"/ai/script": undefined;
	"/ai/voice": undefined;
	"/analytics": undefined;
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

export type RouteId = "/" | "/admin" | "/admin/mock-data" | "/ai" | "/ai/images" | "/ai/music" | "/ai/script" | "/ai/voice" | "/analytics" | "/create" | "/dashboard" | "/demo" | "/forgot-password" | "/login" | "/pricing" | "/profile" | "/projects" | "/register" | "/settings" | "/social" | "/trends" | "/videos" | "/video" | "/video/[videoId]";

export type RouteParams<T extends RouteId> = T extends keyof DynamicRoutes ? DynamicRoutes[T] : Record<string, never>;

export type LayoutParams<T extends RouteId> = Layouts[T] | Record<string, never>;

export type Pathname = "/" | "/admin" | "/admin/mock-data" | "/ai" | "/ai/images" | "/ai/music" | "/ai/script" | "/ai/voice" | "/analytics" | "/create" | "/dashboard" | "/demo" | "/forgot-password" | "/login" | "/pricing" | "/profile" | "/projects" | "/register" | "/settings" | "/social" | "/trends" | "/videos" | "/video" | `/video/${string}` & {};

export type ResolvedPathname = `${"" | `/${string}`}${Pathname}`;

export type Asset = "/manifest.json" | "/service-worker.js";
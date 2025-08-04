/**
 * 格式化日期時間
 */
export function formatDateTime(date: string | Date): string {
	const d = new Date(date);
	return d.toLocaleString('zh-TW', {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	});
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
	const d = new Date(date);
	return d.toLocaleDateString('zh-TW');
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
	const sizes = ['B', 'KB', 'MB', 'GB'];
	if (bytes === 0) return '0 B';
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 格式化數字
 */
export function formatNumber(num: number): string {
	return new Intl.NumberFormat('zh-TW').format(num);
}

/**
 * 截斷文本
 */
export function truncateText(text: string, length: number): string {
	if (text.length <= length) return text;
	return text.substring(0, length) + '...';
}

/**
 * 生成隨機顏色
 */
export function getRandomColor(): string {
	const colors = [
		'#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
		'#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
	];
	return colors[Math.floor(Math.random() * colors.length)];
}

/**
 * 取得狀態顏色
 */
export function getStatusColor(status: string): string {
	const statusColors: { [key: string]: string } = {
		'active': 'green',
		'inactive': 'gray',
		'running': 'blue',
		'completed': 'green',
		'failed': 'red',
		'pending': 'yellow',
		'success': 'green',
		'error': 'red',
		'warning': 'yellow',
		'info': 'blue'
	};
	return statusColors[status.toLowerCase()] || 'gray';
}

/**
 * 取得平台圖示
 */
export function getPlatformIcon(platform: string): string {
	const icons: { [key: string]: string } = {
		'twitter': '🐦',
		'youtube': '📺',
		'instagram': '📸',
		'facebook': '👥',
		'tiktok': '🎵'
	};
	return icons[platform.toLowerCase()] || '🌐';
}

/**
 * 驗證電子郵件
 */
export function isValidEmail(email: string): boolean {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return emailRegex.test(email);
}

/**
 * 驗證URL
 */
export function isValidUrl(url: string): boolean {
	try {
		new URL(url);
		return true;
	} catch {
		return false;
	}
}

/**
 * 深拷貝對象
 */
export function deepClone<T>(obj: T): T {
	return JSON.parse(JSON.stringify(obj));
}

/**
 * 防抖函數
 */
export function debounce<T extends (...args: any[]) => any>(
	func: T,
	wait: number
): (...args: Parameters<T>) => void {
	let timeout: ReturnType<typeof setTimeout>;
	return (...args: Parameters<T>) => {
		clearTimeout(timeout);
		timeout = setTimeout(() => func(...args), wait);
	};
}

/**
 * 節流函數
 */
export function throttle<T extends (...args: any[]) => any>(
	func: T,
	limit: number
): (...args: Parameters<T>) => void {
	let inThrottle: boolean;
	return (...args: Parameters<T>) => {
		if (!inThrottle) {
			func(...args);
			inThrottle = true;
			setTimeout(() => inThrottle = false, limit);
		}
	};
}

/**
 * 從相對時間轉換為毫秒
 */
export function parseTimeToMs(timeStr: string): number {
	const match = timeStr.match(/^(\d+)(s|m|h|d)$/);
	if (!match) return 0;
	
	const value = parseInt(match[1]);
	const unit = match[2];
	
	const multipliers = {
		's': 1000,
		'm': 60 * 1000,
		'h': 60 * 60 * 1000,
		'd': 24 * 60 * 60 * 1000
	};
	
	return value * (multipliers[unit as keyof typeof multipliers] || 0);
}

/**
 * 取得相對時間描述
 */
export function getRelativeTime(date: string | Date): string {
	const now = new Date();
	const target = new Date(date);
	const diffMs = now.getTime() - target.getTime();
	
	const minute = 60 * 1000;
	const hour = 60 * minute;
	const day = 24 * hour;
	const week = 7 * day;
	const month = 30 * day;
	
	if (diffMs < minute) return '剛剛';
	if (diffMs < hour) return `${Math.floor(diffMs / minute)} 分鐘前`;
	if (diffMs < day) return `${Math.floor(diffMs / hour)} 小時前`;
	if (diffMs < week) return `${Math.floor(diffMs / day)} 天前`;
	if (diffMs < month) return `${Math.floor(diffMs / week)} 週前`;
	
	return formatDate(date);
}
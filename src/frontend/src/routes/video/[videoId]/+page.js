import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageLoad} */
export async function load({ params, fetch }) {
  try {
    // 在實際應用中，這裡會從 API 獲取影片資料
    // const response = await fetch(`/api/videos/${params.videoId}`);
    // if (!response.ok) {
    //   throw error(response.status, 'Video not found');
    // }
    // const video = await response.json();
    
    // 目前使用模擬資料
    const video = {
      id: params.videoId,
      title: '如何使用 AI 生成影片內容',
      description: '這是一個展示如何使用人工智慧技術生成高質量影片內容的教學影片。',
      url: '/api/videos/sample-video.mp4',
      thumbnail: 'https://via.placeholder.com/1280x720/4f46e5/ffffff?text=AI+Video+Generation',
      duration: 180,
      views: 15420,
      likes: 892,
      createdAt: '2024-01-15T10:30:00Z',
      updatedAt: '2024-01-20T15:45:00Z',
      author: {
        name: 'AI Creator Studio',
        avatar: 'https://via.placeholder.com/40/6366f1/ffffff?text=AI'
      },
      platforms: ['youtube', 'tiktok', 'instagram'],
      tags: ['AI', '影片生成', '教學', '科技', '創作'],
      status: 'published'
    };
    
    return {
      video
    };
  } catch (err) {
    throw error(404, '找不到影片');
  }
}
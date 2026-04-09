import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
  // Logic lấy dữ liệu chi tiết bài viết từ DB/API theo ID thực tế
  return {
    article: {
      id: params.id,
      title: `Bí quyết dưỡng da chuẩn Elite: Phần ${params.id}`,
      author: 'Micsmo Beauty Lab',
      publishedAt: '2026-04-09',
      content: 'Chào mừng bạn đến với Micsmo Beauty Lab. Hôm nay chúng ta cùng tìm hiểu về quy trình chăm sóc da 10 bước chuẩn Elite V2.2 để đạt được làn da không tì vết...',
      image: '/uploads/img/micsmo/20250729_Clo7Mql2nt.jpeg'
    }
  };
};
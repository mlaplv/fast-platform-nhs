import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  return {
    banners: [
      // Main Carousel Banners (w797)
      { id: '1', image: '/uploads/img/banner/vn-11134258-81ztc-mm7801vsbw94c6@resize_w797_nl.webp' },
      { id: '2', image: '/uploads/img/banner/vn-11134258-81ztc-mmiz6tc047peb7@resize_w797_nl.webp' },
      { id: '3', image: '/uploads/img/banner/sg-11134258-81zu3-mmr6osj4nb41df@resize_w797_nl.webp' },
      // Side Banners (w398)
      { id: '4', image: '/uploads/img/banner/sg-11134258-81ztz-mmr7ei1zauiwc3@resize_w398_nl.webp' },
      { id: '5', image: '/uploads/img/banner/sg-11134258-81zw1-mmr7ejh867lucb@resize_w398_nl.webp' }
    ],
    categories: [
      { id: '1', name: 'Tẩy Trang', icon: '🧼' },
      { id: '2', name: 'Sữa Rửa Mặt', icon: '🧴' },
      { id: '3', name: 'Nước Hoa Hồng', icon: '🌸' },
      { id: '4', name: 'Serum & Essence', icon: '💧' },
      { id: '5', name: 'Kem Dưỡng Da', icon: '✨' },
      { id: '6', name: 'Chống Nắng', icon: '☀️' },
      { id: '7', name: 'Chăm Sóc Mắt', icon: '👁️' },
      { id: '8', name: 'Mặt Nạ', icon: '🎭' },
      { id: '9', name: 'Xịt Khoáng', icon: '🌬️' },
      { id: '10', name: 'Combo Dưỡng Da', icon: '🎁' }
    ],
    products: [
      { id: '1', name: 'Hurry Harry Wrinkle Serum', price: 350000, image: '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg' },
      { id: '2', name: 'White Label Placenta Cream', price: 420000, image: '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png' },
      { id: '3', name: 'Placenta Rich Gold Eye Cream', price: 480000, image: '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-RICH-GOLD-EYE-CREAM-25g-Kem-Mat-Nhau-Thai-Giam-Quang-Tham_. (127).png' },
      { id: '4', name: 'Placenta Essence 180ml', price: 550000, image: '/uploads/img/micsmo/MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-ESSENCE-180ml-TINH-CHAT-CAP-AM-LAM-DIU-DA_. (14.1).png' }
    ],
    videos: [
      { id: '1', url: '/video1.mp4', title: 'Review Kem dưỡng Placenta', likes: 1250 },
      { id: '2', url: '/video2.mp4', title: 'Hướng dẫn dùng Serum xóa nhăn', likes: 2100 }
    ]
  };
};

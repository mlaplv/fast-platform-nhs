import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  return {
    banners: [
      { id: '1', image: '/uploads/img/micsmo/20250729_Clo7Mql2nt.jpeg' },
      { id: '2', image: '/uploads/img/micsmo/20250729_CSBzDOM2TH.jpeg' },
      { id: '3', image: '/uploads/img/micsmo/20250729_zTkx9FSRTL.jpeg' }
    ],
    categories: [
      { id: '1', name: 'Serum', icon: '💧' },
      { id: '2', name: 'Kem dưỡng', icon: '🧴' },
      { id: '3', name: 'Mặt nạ', icon: '🎭' },
      { id: '4', name: 'Chăm sóc mắt', icon: '👁️' }
    ],
    products: [
      { id: '1', name: 'Hurry Harry Wrinkle Serum', price: 350000, image: '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg' },
      { id: '2', name: 'White Label Placenta Cream', price: 420000, image: '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png' },
      { id: '3', name: 'Placenta Rich Gold Eye Cream', price: 480000, image: '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-RICH-GOLD-EYE-CREAM-25g-Kem-Mat-Nhau-Thai-Giam-Quang-Tham_. (127).png' },
      { id: '4', name: 'Placenta Essence 180ml', price: 550000, image: '/uploads/img/micsmo/MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-ESSENCE-180ml-TINH-CHAT-CAP-AM-LAM-DIU-DA_. (14.1).png' }
    ],
    videos: [
      { id: '1', url: '/video1.mp4', title: 'Hurry Harry Serum', likes: 1250, image: '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg' },
      { id: '2', url: '/video2.mp4', title: 'White Label Placenta Cream', likes: 2100, image: '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png' }
    ]
  };
};
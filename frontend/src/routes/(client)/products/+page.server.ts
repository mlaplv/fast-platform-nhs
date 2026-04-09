import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  // Logic lấy danh sách sản phẩm từ DB/API theo chuẩn R00
  return {
    products: Array.from({ length: 20 }).map((_, i) => ({
      id: `${i}`,
      name: `Mỹ phẩm cao cấp Micsmo ${i + 1}`,
      price: 150000 + i * 50000,
      image: `/uploads/img/micsmo/${i % 2 === 0 ? 'Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg' : '-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png'}`
    }))
  };
};
/**
 * Elite V2.2: Viral Intelligence - Automatic Ingredient Icon Recognition
 * Maps ingredient names to relevant viral emojis for enhanced UI/UX.
 */
export function getIngredientIcon(name: string): string {
  if (!name) return '🧬';
  
  const n = name.toLowerCase();
  
  if (n.includes('dipotassium') || n.includes('glycyrrhizate') || n.includes('cam thảo') || n.includes('rễ cây')) return '🪵';
  if (n.includes('collagen') || n.includes('atelocollagen') || n.includes('đàn hồi')) return '🧬';
  if (n.includes('ha') || n.includes('hyaluronic') || n.includes('cấp ẩm') || n.includes('moisture') || n.includes('nước')) return '💧';
  if (n.includes('vitamin c') || n.includes('lemon')) return '🍋';
  if (n.includes('niacinamide') || n.includes('b3') || n.includes('bảo vệ') || n.includes('vách ngăn')) return '🛡️';
  if (n.includes('retinol') || n.includes('chống lão hóa') || n.includes('aging') || n.includes('tái tạo')) return '🌙';
  if (n.includes('trà xanh') || n.includes('tràm trà') || n.includes('thảo mộc') || n.includes('tea') || n.includes('lá')) return '🌿';
  if (n.includes('ceramide') || n.includes('phục hồi') || n.includes('repair') || n.includes('củng cố')) return '🧬';
  if (n.includes('sáng da') || n.includes('white') || n.includes('glow') || n.includes('mờ thâm')) return '✨';
  if (n.includes('chống nắng') || n.includes('sun') || n.includes('uv') || n.includes('spf')) return '☀️';
  if (n.includes('acid') || n.includes('aha') || n.includes('bha') || n.includes('salicylic') || n.includes('peel')) return '🧪';
  if (n.includes('collagen') || n.includes('tế bào gốc') || n.includes('nâng cơ')) return '🧬';
  if (n.includes('rau má') || n.includes('centella') || n.includes('cica')) return '🌱';
  if (n.includes('lựu') || n.includes('pomegranate') || n.includes('đỏ')) return '🍎';
  if (n.includes('hoa hồng') || n.includes('rose') || n.includes('hoa')) return '🌹';
  if (n.includes('mật ong') || n.includes('honey') || n.includes('propolis')) return '🍯';
  if (n.includes('dầu') || n.includes('oil') || n.includes('olive') || n.includes('argan')) return '🫗';
  if (n.includes('than hoạt tính') || n.includes('charcoal') || n.includes('đất sét')) return '🌑';
  
  return '🧬'; // Standard science icon for unknown but technical ingredients
}

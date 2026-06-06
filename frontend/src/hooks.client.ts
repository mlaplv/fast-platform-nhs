import type { HandleClientError } from '@sveltejs/kit';

export const handleError: HandleClientError = ({ error }) => {
  // Suppress sensitive exception details on client-side routing/rendering crashes
  return {
    message: 'Lỗi hệ thống (Internal Error)'
  };
};

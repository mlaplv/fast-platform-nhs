import type { HandleClientError } from "@sveltejs/kit";
import { dev } from "$app/environment";

export const handleError: HandleClientError = ({ error, event }) => {
  console.error('[CLIENT ERROR]', error);
  
  return {
    message: dev && error instanceof Error ? error.message : "Lỗi hệ thống báo cáo (Client Error)",
    stack: dev && error instanceof Error ? error.stack : undefined
  };
};

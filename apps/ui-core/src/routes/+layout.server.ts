/** @type {import('./$types').LayoutServerLoad} */
export const load = async ({ locals }: any) => {
  return {
    user: locals.user,
    tenant: locals.tenant,
    isMobile: locals.isMobile,
  };
};

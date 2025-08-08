export async function load({ url }) {
  const email = url.searchParams.get('email');
  
  return {
    email: email ? decodeURIComponent(email) : ''
  };
}
import { redirect } from 'next/navigation';

export default function HomePage() {
  // Redirect to the real pricing page
  redirect('/pricing.html');
}

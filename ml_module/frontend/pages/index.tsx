import { useRouter } from 'next/router';
import { useEffect } from 'react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirigir a la página de predicciones
    router.push('/predictions');
  }, []);

  return null;
} 
import Image from "next/image";
import App from "./deadLetterDashboard/page";
import type { AppProps } from 'next/app';
import { GoogleOAuthProvider } from '@react-oauth/google';

export default function Home() {
  return (
    
    <div>
      <App />
    </div>
  );
}

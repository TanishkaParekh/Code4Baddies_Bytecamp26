import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBNE4IPtKJdiyRvXG00JWfaokswAeQRJoM",
  authDomain: "code4baddies.firebaseapp.com",
  projectId: "code4baddies",
  storageBucket: "code4baddies.firebasestorage.app",
  messagingSenderId: "202201912175",
  appId: "1:202201912175:web:85c54d1f7be57b19a18e9a"
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
export const auth = getAuth(app);
export default app; 
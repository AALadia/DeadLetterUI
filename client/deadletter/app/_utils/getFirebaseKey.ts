const getFirebaseKey = (apiKey:string) => {
    if (!apiKey) {
        throw new Error("Firebase API key is not defined");
    }
    return {
  apiKey,
  authDomain: "deadletterui.firebaseapp.com",
  projectId: "deadletterui",
  storageBucket: "deadletterui.appspot.com",
  messagingSenderId: "274365361711",
  appId: "1:274365361711:web:a781f68ed1e5c7a2cde0da",
};
}

export default getFirebaseKey;
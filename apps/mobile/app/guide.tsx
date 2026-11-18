import { router } from 'expo-router';
import { Introduction } from '../src/onboarding/Introduction';
export default function Guide() {
  return <Introduction review onContinue={async () => {
    if (router.canGoBack()) router.back();
    else router.replace('/');
  }} />;
}

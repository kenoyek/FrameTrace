import { NativeModule, requireOptionalNativeModule } from 'expo-modules-core';
type ShareEvents = { onShare: (event: { error?: string }) => void };
export declare class ShareBridge extends NativeModule<ShareEvents> {
  peek(): Promise<unknown>;
  consume(id: string): Promise<unknown>;
  discard(id: string): Promise<void>;
}
export const shareBridge = requireOptionalNativeModule<ShareBridge>('FrameTraceShare');

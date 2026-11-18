import * as ImagePicker from 'expo-image-picker';
import { PermissionsAndroid, Platform } from 'react-native';

// Picker metadata is an early UX check. The server independently probes every upload.
export function validateVideo(video: ImagePicker.ImagePickerAsset): void {
  if (video.type !== 'video' || !/^(file|content):\/\//.test(video.uri)) {
    throw new Error('Choose a local video file.');
  }
  if (video.duration != null && (!Number.isFinite(video.duration) || video.duration < 1000 || video.duration > 30000)) {
    throw new Error('Choose a clip between 1 and 30 seconds. Trimming is not available in this build yet.');
  }
  if (video.fileSize != null && (!Number.isFinite(video.fileSize) || video.fileSize <= 0 || video.fileSize > 50 * 1024 * 1024)) {
    throw new Error('Choose a non-empty video no larger than 50 MB.');
  }
  if (!Number.isFinite(video.width) || !Number.isFinite(video.height) || video.width <= 0 || video.height <= 0 || video.width * video.height > 3840 * 2160) {
    throw new Error('Choose a video with a resolution no higher than 4K.');
  }
}

export async function recordVideo(): Promise<ImagePicker.ImagePickerAsset | null> {
  if (Platform.OS === 'web') throw new Error('Record a clip in the Android or iOS app.');
  const camera = await ImagePicker.requestCameraPermissionsAsync();
  if (!camera.granted) {
    throw new Error(camera.canAskAgain
      ? 'Camera access is needed to record. You can also choose a gallery video.'
      : 'Enable camera access for FrameTrace in device Settings, or choose a gallery video.');
  }
  // iOS requests microphone access in its system camera, using NSMicrophoneUsageDescription.
  if (Platform.OS === 'android') {
    const microphone = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO);
    if (microphone !== PermissionsAndroid.RESULTS.GRANTED) {
      throw new Error('Microphone access is needed to record video with sound. Enable it in device Settings, or choose a gallery video.');
    }
  }
  const result = await ImagePicker.launchCameraAsync({
    mediaTypes: ['videos'], allowsEditing: false, videoMaxDuration: 30,
    videoQuality: ImagePicker.UIImagePickerControllerQualityType.Medium,
  });
  if (result.canceled) return null;
  const video = result.assets[0];
  if (!video) throw new Error('The camera did not return a video. Please try again.');
  validateVideo(video);
  return video;
}

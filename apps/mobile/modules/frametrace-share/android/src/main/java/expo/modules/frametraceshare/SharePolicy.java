package expo.modules.frametraceshare;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.net.URI;

/** Pure Java intake rules, shared with the Android implementation and JVM tests. */
public final class SharePolicy {
  public static final long MAX_BYTES = 50L * 1024 * 1024;
  public static final long TTL_MS = 24L * 60 * 60 * 1000;
  public static final int MAX_ITEMS = 3;
  private SharePolicy() {}

  public static void requireId(String id) {
    if (id == null || !id.matches("[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"))
      throw new IllegalArgumentException("Invalid shared item.");
  }

  public static boolean isContainer(byte[] header) {
    return header.length >= 12 && header[4] == 'f' && header[5] == 't' && header[6] == 'y' && header[7] == 'p';
  }

  public static String linkHost(String text) {
    try {
      if (text == null || text.length() > 2048) return null;
      URI uri = new URI(text.trim());
      String host = uri.getHost();
      if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getUserInfo() != null || host == null ||
          host.length() > 253 || !host.matches("[A-Za-z0-9.-]+")) return null;
      return host.toLowerCase(java.util.Locale.ROOT);
    } catch (Exception ignored) { return null; }
  }

  public static long copyBounded(InputStream input, OutputStream output, long maximum) throws IOException {
    long total = 0;
    byte[] buffer = new byte[64 * 1024];
    long deadline = System.nanoTime() + 15_000_000_000L;
    int count;
    while ((count = input.read(buffer)) != -1) {
      if (System.nanoTime() > deadline) throw new IOException("Import took too long. Try another video.");
      total += count;
      if (total > maximum) throw new IOException("Choose a video smaller than 50 MB.");
      output.write(buffer, 0, count);
    }
    if (total < 12) throw new IOException("Choose a valid MP4 or MOV video.");
    return total;
  }
}

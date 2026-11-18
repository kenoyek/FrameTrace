package expo.modules.frametraceshare;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Arrays;

/** Runs the actual intake implementation on the JVM; no Android mocks or zero-test runner. */
public final class SharePolicyTest {
  public static void main(String[] args) throws Exception {
    byte[] clip = new byte[32];
    clip[4] = 'f'; clip[5] = 't'; clip[6] = 'y'; clip[7] = 'p';
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    long copied = SharePolicy.copyBounded(new ByteArrayInputStream(clip), output, 32);
    check(copied == 32 && Arrays.equals(clip, output.toByteArray()), "Exact-limit copy changed video bytes");
    output = new ByteArrayOutputStream();
    try {
      SharePolicy.copyBounded(new ByteArrayInputStream(clip), output, 31);
      throw new AssertionError("Oversize media accepted");
    } catch (IOException expected) { check(output.size() <= 31, "Wrote past byte limit"); }
    check(SharePolicy.isContainer(clip) && !SharePolicy.isContainer(new byte[32]) && !SharePolicy.isContainer(new byte[4]), "Container signature validation failed");
    check("example.com".equals(SharePolicy.linkHost("https://Example.com/private?token=never-retain")), "Hostname extraction failed");
    for (String invalid : new String[] {"http://example.com", "javascript:alert(1)", "file:///tmp/video.mp4", "https://user:secret@example.com", "some text"})
      check(SharePolicy.linkHost(invalid) == null, "Unsafe URL accepted");
    SharePolicy.requireId("12345678-1234-1234-1234-123456789abc");
    try { SharePolicy.requireId("../../outside"); throw new AssertionError("Traversal accepted"); }
    catch (IllegalArgumentException expected) { /* confined to generated UUID folders */ }
    System.out.println("6 native share-policy groups passed (real JVM byte/URL/path validation).");
  }
  private static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
}

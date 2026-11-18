package expo.modules.frametraceshare

import android.content.Intent
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import expo.modules.kotlin.Promise
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import org.json.JSONObject
import java.io.File
import java.util.UUID
import java.util.concurrent.Executors

class FrameTraceShareModule : Module() {
  private val executor = Executors.newSingleThreadExecutor()
  private val seen = java.util.WeakHashMap<Intent, Boolean>()
  private val root: File get() = File(requireNotNull(appContext.reactContext).cacheDir, "FrameTraceShares").also { it.mkdirs() }

  override fun definition() = ModuleDefinition {
    Name("FrameTraceShare")
    Events("onShare")
    OnCreate { capture(appContext.currentActivity?.intent) }
    OnActivityEntersForeground { capture(appContext.currentActivity?.intent) }
    OnNewIntent { intent -> capture(intent) }
    OnDestroy { executor.shutdown() }
    AsyncFunction("peek") { promise: Promise ->
      capture(appContext.currentActivity?.intent)
      executor.execute {
        try {
          prune()
          val record = root.listFiles()?.filter { File(it, "payload.json").isFile }?.sortedBy { it.name }
            ?.map { read(it) }?.minByOrNull { it.optLong("createdAt") }
          promise.resolve(record?.let { jsonMap(it) })
        } catch (_: Exception) { promise.reject("IMPORT_UNAVAILABLE", "Shared videos could not be read.", null) }
      }
    }
    AsyncFunction("consume") { id: String, promise: Promise ->
      executor.execute {
        try {
          SharePolicy.requireId(id)
          prune()
          val folder = File(root, id)
          val payload = read(folder)
          if (payload.optString("kind") == "video") {
            val file = File(folder, "clip.mp4")
            require(file.isFile) { "The shared video expired. Share it again." }
            payload.put("uri", Uri.fromFile(file).toString())
          }
          promise.resolve(jsonMap(payload))
        } catch (_: Exception) { promise.reject("IMPORT_EXPIRED", "This shared item is no longer available. Share it again.", null) }
      }
    }
    AsyncFunction("discard") { id: String, promise: Promise ->
      executor.execute {
        try {
          SharePolicy.requireId(id)
          File(root, id).deleteRecursively()
          promise.resolve(null)
          sendEvent("onShare", emptyMap<String, Any>())
        } catch (_: Exception) { promise.reject("IMPORT_UNAVAILABLE", "Shared item could not be removed.", null) }
      }
    }
  }

  private fun read(folder: File): JSONObject {
    SharePolicy.requireId(folder.name)
    val manifest = File(folder, "payload.json")
    require(manifest.length() in 1..8192) { "Invalid shared item." }
    return JSONObject(manifest.readText()).put("id", folder.name)
  }
  private fun jsonMap(value: JSONObject): Map<String, Any?> = value.keys().asSequence().associateWith { value.get(it).let { v -> if (v == JSONObject.NULL) null else v } }
  private fun prune() {
    val cutoff = System.currentTimeMillis() - SharePolicy.TTL_MS
    root.listFiles()?.filter { it.lastModified() < cutoff }?.forEach { it.deleteRecursively() }
  }
  private fun publish(folder: File, payload: JSONObject) {
    val pending = File(folder, "payload.tmp")
    pending.writeText(payload.toString())
    check(pending.renameTo(File(folder, "payload.json")))
    sendEvent("onShare", emptyMap<String, Any>())
  }
  private fun capture(intent: Intent?) {
    if (intent == null || intent.action !in listOf(Intent.ACTION_SEND, Intent.ACTION_SEND_MULTIPLE)) return
    synchronized(this) {
      if (seen.containsKey(intent)) return
      seen[intent] = true
    }
    val action = intent.action
    // Intent.setData clears type: snapshot MIME before clearing borrowed intent data.
    val mime = intent.type ?: ""
    val hasReadGrant = intent.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0
    val envelope: Pair<Uri?, String?>? = try {
      val uri = if (Build.VERSION.SDK_INT >= 33) intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
        else @Suppress("DEPRECATION") (intent.getParcelableExtra(Intent.EXTRA_STREAM) as? Uri)
      val content = uri ?: intent.clipData?.takeIf { it.itemCount == 1 }?.getItemAt(0)?.uri ?: intent.data?.takeIf { it.scheme == "content" }
      val text = intent.getStringExtra(Intent.EXTRA_TEXT) ?: intent.clipData?.takeIf { it.itemCount == 1 }?.getItemAt(0)?.text?.toString() ?: intent.data?.toString()
      Pair(content, text)
    } catch (_: Exception) { null } // Malformed external parcelables never crash the activity.
    val content = envelope?.first
    val text = envelope?.second
    intent.replaceExtras(null as android.os.Bundle?)
    intent.clipData = null
    intent.data = null
    intent.action = Intent.ACTION_MAIN
    executor.execute {
      prune()
      // Never evict a fresh selection that may be uploading or waiting for consent.
      if ((root.listFiles()?.size ?: 0) >= SharePolicy.MAX_ITEMS) {
        sendEvent("onShare", mapOf("error" to "Finish or dismiss earlier shared videos first, then share again."))
        return@execute
      }
      val id = UUID.randomUUID().toString()
      val folder = File(root, id).also { it.mkdir() }
      val payload = JSONObject().put("id", id).put("createdAt", System.currentTimeMillis())
      try {
        require(envelope != null) { "Share an MP4 or MOV video file." }
        require(action == Intent.ACTION_SEND) { "Share one video at a time." }
        if (content != null && content.scheme == "content") {
          val context = requireNotNull(appContext.reactContext)
          require(hasReadGrant) { "The shared video permission expired. Share it again." }
          require(content.authority?.substringAfterLast('@') != context.packageName && content.authority?.substringAfterLast('@')?.startsWith(context.packageName + ".") != true) {
            "Choose this video from your gallery instead."
          }
          require(mime.startsWith("video/")) { "Share an MP4 or MOV video file." }
          val destination = File(folder, "clip.mp4")
          val length = context.contentResolver.openInputStream(content)?.use { input ->
            destination.outputStream().use { output -> SharePolicy.copyBounded(input, output, SharePolicy.MAX_BYTES) }
          } ?: error("The video permission expired. Share it again.")
          require(SharePolicy.isContainer(destination.inputStream().use { val header = ByteArray(12); java.io.DataInputStream(it).readFully(header); header })) { "Choose a valid MP4 or MOV video." }
          val reader = MediaMetadataRetriever()
          try {
            reader.setDataSource(destination.absolutePath)
            val duration = reader.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0
            val width = reader.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull() ?: 0
            val height = reader.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull() ?: 0
            require(duration in 1000L..30000L) { "Share a clip between 1 and 30 seconds." }
            require(width > 0 && height > 0 && width.toLong() * height <= 3840L * 2160) { "This video resolution is unsupported." }
            payload.put("kind", "video").put("fileSize", length).put("durationMs", duration)
              .put("width", width).put("height", height).put("mimeType", "video/mp4")
          } finally { reader.release() }
        } else {
          val host = SharePolicy.linkHost(text ?: content?.toString())
          require(host != null) { "Share an MP4 or MOV video file." }
          // No query/path tokens are retained. No platform URL is downloaded.
          payload.put("kind", "link").put("sourceHost", host)
        }
        publish(folder, payload)
      } catch (error: Exception) {
        File(folder, "clip.mp4").delete()
        // Only our own validation messages are shown; provider URI/errors stay private.
        val safeMessages = setOf("Share one video at a time.", "Share an MP4 or MOV video file.",
          "Choose a valid MP4 or MOV video.", "Share a clip between 1 and 30 seconds.",
          "This video resolution is unsupported.", "Choose a video smaller than 50 MB.",
          "Import took too long. Try another video.", "The shared video permission expired. Share it again.",
          "Choose this video from your gallery instead.")
        val message = error.message?.takeIf { it in safeMessages }
          ?: "The video could not be imported. Check access and share it again."
        publish(folder, payload.put("kind", "error").put("message", message))
      }
    }
  }
}

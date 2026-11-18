import ExpoModulesCore
import Foundation

public class FrameTraceShareModule: Module {
  private let files = FileManager.default
  private let inboxQueue = DispatchQueue(label: "app.frametrace.share-inbox", qos: .userInitiated)
  private let ttl: TimeInterval = 24 * 3600
  private var cache: URL {
    files.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("FrameTraceShares", isDirectory: true)
  }
  private func group() throws -> URL {
    guard let name = Bundle.main.object(forInfoDictionaryKey: "FrameTraceAppGroup") as? String,
          let url = files.containerURL(forSecurityApplicationGroupIdentifier: name) else {
      throw NSError(domain: "FrameTraceShare", code: 1, userInfo: [NSLocalizedDescriptionKey: "Sharing is not configured in this build."])
    }
    return url.appendingPathComponent("FrameTraceShareInbox", isDirectory: true)
  }
  private func prepare(_ root: URL) throws {
    try files.createDirectory(at: root, withIntermediateDirectories: true)
    for folder in try files.contentsOfDirectory(at: root, includingPropertiesForKeys: [.contentModificationDateKey]) {
      if let modified = try? folder.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate,
         Date().timeIntervalSince(modified) > ttl { try? files.removeItem(at: folder) }
    }
  }
  private func payload(_ folder: URL) throws -> [String: Any] {
    let data = try Data(contentsOf: folder.appendingPathComponent("payload.json"), options: .mappedIfSafe)
    guard data.count < 8192, let value = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
      throw NSError(domain: "FrameTraceShare", code: 2)
    }
    return value
  }
  public func definition() -> ModuleDefinition {
    Name("FrameTraceShare")
    Events("onShare")
    AsyncFunction("peek") { () throws -> [String: Any]? in
      let shared = try self.group()
      try self.prepare(shared)
      try self.prepare(self.cache)
      let folders = (try self.files.contentsOfDirectory(at: shared, includingPropertiesForKeys: nil)) +
                    (try self.files.contentsOfDirectory(at: self.cache, includingPropertiesForKeys: nil))
      return folders.compactMap { try? self.payload($0) }.sorted {
        ($0["createdAt"] as? Double ?? 0) < ($1["createdAt"] as? Double ?? 0)
      }.first
    }.runOnQueue(inboxQueue)
    AsyncFunction("consume") { (id: String) throws -> [String: Any] in
      guard UUID(uuidString: id) != nil else { throw NSError(domain: "FrameTraceShare", code: 3) }
      let shared = try self.group()
      try self.prepare(shared)
      try self.prepare(self.cache)
      let source = shared.appendingPathComponent(id, isDirectory: true)
      let local = self.cache.appendingPathComponent(id, isDirectory: true)
      if !self.files.fileExists(atPath: local.appendingPathComponent("payload.json").path) {
        let count = try self.files.contentsOfDirectory(at: self.cache, includingPropertiesForKeys: nil).count
        guard count < 3 else { throw NSError(domain: "FrameTraceShare", code: 4, userInfo: [NSLocalizedDescriptionKey: "Finish or dismiss earlier shared videos first."]) }
        // Copy the complete directory into the host cache before deleting the shared copy.
        if self.files.fileExists(atPath: local.path) { try self.files.removeItem(at: local) }
        try self.files.copyItem(at: source, to: local)
        _ = try self.payload(local)
        try self.files.removeItem(at: source)
      }
      var value = try self.payload(local)
      if value["kind"] as? String == "video" {
        let clip = local.appendingPathComponent("clip.mp4")
        guard self.files.fileExists(atPath: clip.path) else { throw NSError(domain: "FrameTraceShare", code: 5) }
        value["uri"] = clip.absoluteString
      }
      return value
    }.runOnQueue(inboxQueue)
    AsyncFunction("discard") { (id: String) throws in
      guard UUID(uuidString: id) != nil else { throw NSError(domain: "FrameTraceShare", code: 3) }
      let shared = try self.group()
      for root in [shared, self.cache] {
        let path = root.appendingPathComponent(id, isDirectory: true)
        if self.files.fileExists(atPath: path.path) { try self.files.removeItem(at: path) }
      }
    }.runOnQueue(inboxQueue)
  }
}

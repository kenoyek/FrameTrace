import UIKit
import UniformTypeIdentifiers
import AVFoundation

private enum ImportFailure: Error {
  case unsupported, limit, duration, capacity, cancelled
  var message: String {
    switch self {
    case .unsupported: return "Share one MP4 or MOV video, or choose a clip from your gallery."
    case .limit: return "Choose a video smaller than 50 MB with a supported resolution."
    case .duration: return "Share a clip between 1 and 30 seconds."
    case .capacity: return "Open FrameTrace and finish or dismiss earlier shared videos first."
    case .cancelled: return "Import cancelled."
    }
  }
}

final class ShareViewController: UIViewController {
  private let files = FileManager.default
  private let titleLabel = UILabel()
  private let detail = UILabel()
  private let save = UIButton(type: .system)
  private let cancel = UIButton(type: .system)
  private var work: Task<Void, Never>?
  private var providerProgress: Progress?

  override func viewDidLoad() {
    super.viewDidLoad()
    view.backgroundColor = .systemBackground
    titleLabel.text = "Save to FrameTrace"
    titleLabel.font = .preferredFont(forTextStyle: .title1)
    titleLabel.adjustsFontForContentSizeCategory = true
    detail.text = "Save this clip privately, then open FrameTrace to review it. Nothing uploads until you tap Identify."
    detail.font = .preferredFont(forTextStyle: .body)
    detail.adjustsFontForContentSizeCategory = true
    detail.numberOfLines = 0
    titleLabel.numberOfLines = 0
    save.setTitle("Save for review", for: .normal)
    save.titleLabel?.font = .preferredFont(forTextStyle: .headline)
    save.titleLabel?.adjustsFontForContentSizeCategory = true
    save.addTarget(self, action: #selector(saveTapped), for: .touchUpInside)
    cancel.setTitle("Cancel", for: .normal)
    cancel.addTarget(self, action: #selector(cancelTapped), for: .touchUpInside)
    let stack = UIStackView(arrangedSubviews: [titleLabel, detail, save, cancel])
    stack.axis = .vertical
    stack.spacing = 24
    stack.translatesAutoresizingMaskIntoConstraints = false
    let scroll = UIScrollView()
    scroll.translatesAutoresizingMaskIntoConstraints = false
    view.addSubview(scroll)
    scroll.addSubview(stack)
    NSLayoutConstraint.activate([
      scroll.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
      scroll.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor),
      scroll.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
      scroll.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor),
      stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor, constant: 24),
      stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor, constant: -24),
      stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor, constant: 28),
      stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor, constant: -24),
      stack.widthAnchor.constraint(equalTo: scroll.frameLayoutGuide.widthAnchor, constant: -48),
      save.heightAnchor.constraint(greaterThanOrEqualToConstant: 48),
      cancel.heightAnchor.constraint(greaterThanOrEqualToConstant: 48)
    ])
    preferredContentSize = CGSize(width: 380, height: 360)
  }

  @objc private func cancelTapped() {
    work?.cancel()
    providerProgress?.cancel()
    extensionContext?.cancelRequest(withError: NSError(domain: "FrameTraceShare", code: 1))
  }

  @objc private func saveTapped() {
    save.isEnabled = false
    detail.text = "Saving a private copy…"
    work = Task {
      do {
        try await importItem()
        titleLabel.text = "Ready for review"
        detail.text = "Open FrameTrace to preview this item, then tap Identify when you’re ready. No clip has been uploaded."
        cancel.isHidden = true
        save.setTitle("Done", for: .normal)
        save.removeTarget(self, action: #selector(saveTapped), for: .touchUpInside)
        save.addTarget(self, action: #selector(doneTapped), for: .touchUpInside)
      } catch {
        detail.text = (error as? ImportFailure)?.message ?? "The item could not be imported. Check access and share it again."
      }
      save.isEnabled = true
    }
  }

  @objc private func doneTapped() {
    // A Share extension never traverses responders or opens UIApplication/the host app.
    extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
  }

  private func importItem() async throws {
    guard let group = Bundle.main.object(forInfoDictionaryKey: "FrameTraceAppGroup") as? String,
          let container = files.containerURL(forSecurityApplicationGroupIdentifier: group) else { throw ImportFailure.unsupported }
    let root = container.appendingPathComponent("FrameTraceShareInbox", isDirectory: true)
    try files.createDirectory(at: root, withIntermediateDirectories: true)
    for old in try files.contentsOfDirectory(at: root, includingPropertiesForKeys: [.contentModificationDateKey]) {
      if let modified = try? old.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate,
         Date().timeIntervalSince(modified) > 24 * 3600 { try? files.removeItem(at: old) }
    }
    let id = UUID().uuidString.lowercased()
    let folder = root.appendingPathComponent(id, isDirectory: true)
    var coordinationError: NSError?
    var reservationError: Error?
    // Multiple extension instances share one quota; reserve the directory under a file coordinator.
    NSFileCoordinator().coordinate(writingItemAt: root, options: .forMerging, error: &coordinationError) { coordinated in
      do {
        guard try self.files.contentsOfDirectory(at: coordinated, includingPropertiesForKeys: nil).count < 3 else { throw ImportFailure.capacity }
        try self.files.createDirectory(at: folder, withIntermediateDirectories: false,
          attributes: [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication])
      } catch { reservationError = error }
    }
    if let error = coordinationError { throw error }
    if let error = reservationError { throw error }
    let providers = (extensionContext?.inputItems as? [NSExtensionItem] ?? []).flatMap { $0.attachments ?? [] }
    let videos = providers.filter { $0.hasItemConformingToTypeIdentifier(UTType.movie.identifier) }
    var committed = false
    defer { if !committed { try? files.removeItem(at: folder) } }
    var payload: [String: Any] = ["id": id, "createdAt": Date().timeIntervalSince1970 * 1000]
    if videos.count == 1 {
      let destination = folder.appendingPathComponent("clip.mp4")
      try await copyVideo(videos[0], to: destination)
      let asset = AVURLAsset(url: destination)
      let seconds = CMTimeGetSeconds(try await asset.load(.duration))
      guard seconds.isFinite && seconds >= 1 && seconds <= 30 else { throw ImportFailure.duration }
      let tracks = try await asset.loadTracks(withMediaType: .video)
      guard let track = tracks.first else { throw ImportFailure.unsupported }
      let size = try await track.load(.naturalSize)
      let width = Int(abs(size.width)), height = Int(abs(size.height))
      guard width > 0 && height > 0 && Int64(width) * Int64(height) <= 3840 * 2160 else { throw ImportFailure.limit }
      let bytes = try destination.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
      payload.merge(["kind": "video", "fileSize": bytes, "durationMs": seconds * 1000,
                     "width": width, "height": height, "mimeType": "video/mp4"]) { _, next in next }
    } else if videos.isEmpty, providers.count == 1 {
      let provider = providers[0]
      let type = provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) ? UTType.url.identifier : UTType.text.identifier
      let text: String = try await withCheckedThrowingContinuation { continuation in
        providerProgress = provider.loadItem(forTypeIdentifier: type, options: nil) { item, _ in
          if let url = item as? URL { continuation.resume(returning: url.absoluteString) }
          else if let value = item as? String { continuation.resume(returning: value) }
          else { continuation.resume(throwing: ImportFailure.unsupported) }
        }
      }
      guard text.count <= 2048, let url = URL(string: text.trimmingCharacters(in: .whitespacesAndNewlines)),
            url.scheme?.lowercased() == "https", url.user == nil, url.password == nil,
            let host = url.host, host.count <= 253 else { throw ImportFailure.unsupported }
      // Retain only the hostname; private URL paths/query tokens never enter the inbox.
      payload.merge(["kind": "link", "sourceHost": host.lowercased()]) { _, next in next }
    } else { throw ImportFailure.unsupported }
    try Task.checkCancellation()
    let data = try JSONSerialization.data(withJSONObject: payload)
    try data.write(to: folder.appendingPathComponent("payload.json"), options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    committed = true
  }

  private func copyVideo(_ provider: NSItemProvider, to destination: URL) async throws {
    try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
      providerProgress = provider.loadFileRepresentation(forTypeIdentifier: UTType.movie.identifier) { source, _ in
        guard let source, source.isFileURL else { continuation.resume(throwing: ImportFailure.unsupported); return }
        let scoped = source.startAccessingSecurityScopedResource()
        defer { if scoped { source.stopAccessingSecurityScopedResource() } }
        do {
          // The provider's temporary file is copied before this callback returns.
          guard let input = InputStream(url: source), let output = OutputStream(url: destination, append: false) else { throw ImportFailure.unsupported }
          input.open(); output.open()
          defer { input.close(); output.close() }
          let deadline = Date().addingTimeInterval(15)
          var buffer = [UInt8](repeating: 0, count: 64 * 1024)
          var total = 0
          while true {
            let count = input.read(&buffer, maxLength: buffer.count)
            if count == 0 { break }
            guard count > 0, Date() < deadline else { throw ImportFailure.unsupported }
            total += count
            guard total <= 50 * 1024 * 1024 else { throw ImportFailure.limit }
            var offset = 0
            while offset < count {
              let written = buffer.withUnsafeBytes { bytes in
                output.write(bytes.baseAddress!.advanced(by: offset).assumingMemoryBound(to: UInt8.self), maxLength: count - offset)
              }
              guard written > 0 else { throw ImportFailure.unsupported }
              offset += written
            }
          }
          guard total >= 12 else { throw ImportFailure.unsupported }
          let handle = try FileHandle(forReadingFrom: destination)
          defer { try? handle.close() }
          let header = try handle.read(upToCount: 12) ?? Data()
          guard header.count >= 12 && String(data: header[4..<8], encoding: .ascii) == "ftyp" else { throw ImportFailure.unsupported }
          try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: destination.path)
          continuation.resume(returning: ())
        } catch { continuation.resume(throwing: error) }
      }
    }
  }
}

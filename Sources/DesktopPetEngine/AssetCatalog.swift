import AppKit
import Foundation

private struct AssetManifest: Decodable {
    let version: Int
    let canvasWidth: Int
    let canvasHeight: Int
    let animations: [String: AnimationMetadata]
}

private struct AnimationMetadata: Decodable {
    let fps: Double
    let frameCount: Int
    let directionFrames: [String: Int]?
}

enum AssetCatalogError: LocalizedError {
    case resourceFolderMissing
    case manifestMissing
    case requiredAnimationMissing(PetAction)
    case noFrames(PetAction)

    var errorDescription: String? {
        switch self {
        case .resourceFolderMissing:
            return "找不到应用素材目录"
        case .manifestMissing:
            return "找不到或无法读取素材 manifest.json"
        case .requiredAnimationMissing(let action):
            return "缺少必需动作：\(action.chineseTitle)"
        case .noFrames(let action):
            return "动作“\(action.chineseTitle)”没有 PNG 帧"
        }
    }
}

final class AnimationClip {
    let action: PetAction
    let fps: Double
    let frameURLs: [URL]
    let directionFrames: [String: Int]

    private let cache = NSCache<NSNumber, NSImage>()

    init(action: PetAction, fps: Double, frameURLs: [URL], directionFrames: [String: Int]) {
        self.action = action
        self.fps = max(1, fps)
        self.frameURLs = frameURLs
        self.directionFrames = directionFrames
        cache.countLimit = 140
    }

    var frameCount: Int { frameURLs.count }

    func image(at requestedIndex: Int) -> NSImage? {
        guard !frameURLs.isEmpty else { return nil }
        let index = min(max(0, requestedIndex), frameURLs.count - 1)
        let key = NSNumber(value: index)
        if let cached = cache.object(forKey: key) {
            return cached
        }
        guard let image = NSImage(contentsOf: frameURLs[index]) else { return nil }
        cache.setObject(image, forKey: key)
        return image
    }

    func image(for direction: CursorDirection) -> NSImage? {
        let index = directionFrames[direction.rawValue]
            ?? directionFrames[CursorDirection.center.rawValue]
            ?? 0
        return image(at: index)
    }
}

final class AssetCatalog {
    let canvasSize: NSSize

    private let clips: [PetAction: AnimationClip]

    init() throws {
        #if SWIFT_PACKAGE
        let bundleRoot = Bundle.module.resourceURL
        #else
        let bundleRoot = Bundle.main.resourceURL
        #endif
        guard let bundleRoot else {
            throw AssetCatalogError.resourceFolderMissing
        }
        let root = bundleRoot.appendingPathComponent("Assets", isDirectory: true)
        let manifestURL = root.appendingPathComponent("manifest.json")
        guard let data = try? Data(contentsOf: manifestURL),
              let manifest = try? JSONDecoder().decode(AssetManifest.self, from: data) else {
            throw AssetCatalogError.manifestMissing
        }

        canvasSize = NSSize(width: manifest.canvasWidth, height: manifest.canvasHeight)

        var loaded: [PetAction: AnimationClip] = [:]
        for action in PetAction.allCases {
            guard let metadata = manifest.animations[action.rawValue] else { continue }
            let folder = root.appendingPathComponent(action.rawValue, isDirectory: true)
            let urls = (try? FileManager.default.contentsOfDirectory(
                at: folder,
                includingPropertiesForKeys: nil,
                options: [.skipsHiddenFiles]
            ))?
                .filter { $0.pathExtension.lowercased() == "png" }
                .sorted { $0.lastPathComponent < $1.lastPathComponent } ?? []

            guard !urls.isEmpty else { continue }
            let expectedCount = metadata.frameCount
            if expectedCount != urls.count {
                NSLog("动作 %@：manifest 标记 %d 帧，实际找到 %d 帧", action.rawValue, expectedCount, urls.count)
            }
            loaded[action] = AnimationClip(
                action: action,
                fps: metadata.fps,
                frameURLs: urls,
                directionFrames: metadata.directionFrames ?? [:]
            )
        }
        clips = loaded
    }

    func clip(for action: PetAction) -> AnimationClip? {
        clips[action]
    }

    func hasClip(for action: PetAction) -> Bool {
        clips[action] != nil
    }

    func frameCount(for action: PetAction) -> Int {
        clips[action]?.frameCount ?? 0
    }

    func validateRequiredAssets() throws {
        for action in [PetAction.idle, .walk, .dance, .playBall, .eat, .drink, .yawn, .frustrated, .crying, .shy, .happy, .rowing, .meditation] {
            guard let clip = clips[action] else {
                throw AssetCatalogError.requiredAnimationMissing(action)
            }
            guard clip.frameCount > 0 else {
                throw AssetCatalogError.noFrames(action)
            }
            guard clip.image(at: 0) != nil else {
                throw AssetCatalogError.noFrames(action)
            }
        }
    }
}

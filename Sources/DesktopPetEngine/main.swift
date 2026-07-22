import AppKit
import Darwin

if CommandLine.arguments.contains("--self-test") {
    do {
        let catalog = try AssetCatalog()
        try catalog.validateRequiredAssets()
        print(
            "素材自检通过：待机 \(catalog.frameCount(for: .idle)) 帧，" +
            "走路 \(catalog.frameCount(for: .walk)) 帧，" +
            "跳舞 \(catalog.frameCount(for: .dance)) 帧，" +
            "玩球 \(catalog.frameCount(for: .playBall)) 帧，" +
            "吃饭 \(catalog.frameCount(for: .eat)) 帧，" +
            "喝水 \(catalog.frameCount(for: .drink)) 帧，" +
            "打哈欠 \(catalog.frameCount(for: .yawn)) 帧，" +
            "抓狂 \(catalog.frameCount(for: .frustrated)) 帧，" +
            "哭泣 \(catalog.frameCount(for: .crying)) 帧，" +
            "害羞 \(catalog.frameCount(for: .shy)) 帧，" +
            "开心 \(catalog.frameCount(for: .happy)) 帧，" +
            "划船 \(catalog.frameCount(for: .rowing)) 帧，" +
            "冥想 \(catalog.frameCount(for: .meditation)) 帧"
        )
        exit(EXIT_SUCCESS)
    } catch {
        fputs("素材自检失败：\(error.localizedDescription)\n", stderr)
        exit(EXIT_FAILURE)
    }
}

let application = NSApplication.shared
let appDelegate = AppDelegate()
application.delegate = appDelegate
application.setActivationPolicy(.accessory)
application.run()

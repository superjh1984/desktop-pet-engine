import AppKit

private struct CursorThemeManifest: Decodable {
    let version: Int
    let themes: [CursorThemeDefinition]
}

private struct CursorThemeTitle: Decodable {
    let english: String
    let simplifiedChinese: String

    enum CodingKeys: String, CodingKey {
        case english = "en"
        case simplifiedChinese = "zh-Hans"
    }

    var localized: String {
        let prefersChinese = Locale.preferredLanguages.first?
            .lowercased()
            .hasPrefix("zh") ?? false
        return prefersChinese
            ? "\(simplifiedChinese) / \(english)"
            : "\(english) / \(simplifiedChinese)"
    }
}

private struct CursorThemeDefinition: Decodable {
    let id: String
    let title: CursorThemeTitle
    let capeFile: String
    let capeIdentifier: String
    let actions: [String]?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case capeFile = "cape_file"
        case capeIdentifier = "cape_identifier"
        case actions
    }
}

extension Notification.Name {
    static let cursorThemeDidChange = Notification.Name("CursorThemeDidChange")
}

private enum CursorThemeError: LocalizedError {
    case unsupportedManifestVersion(Int)
    case invalidConfiguration(String)
    case bundledCapeMissing(String)
    case invalidCape(String)
    case mousecapeMissing
    case mousecloakFailed(String)

    var errorDescription: String? {
        switch self {
        case .unsupportedManifestVersion(let version):
            return "不支持鼠标主题配置版本 \(version) / Unsupported cursor theme manifest version \(version)"
        case .invalidConfiguration(let details):
            return "鼠标主题配置无效：\(details) / Invalid cursor theme configuration: \(details)"
        case .bundledCapeMissing(let name):
            return "找不到鼠标主题：\(name) / Cursor theme is missing: \(name)"
        case .invalidCape(let name):
            return "鼠标主题文件无效：\(name) / Invalid cursor theme file: \(name)"
        case .mousecapeMissing:
            return """
            没有找到 Mousecape。请自行安装并打开一次；Apple 芯片 Mac 可能还需要 Rosetta。
            Mousecape was not found. Install and open it once; Apple silicon Macs may also need Rosetta.
            """
        case .mousecloakFailed(let details):
            return """
            Mousecape 没有成功应用鼠标主题，请先单独打开 Mousecape 完成初始化。
            Mousecape could not apply the cursor theme. Open Mousecape once to finish setup.

            \(details)
            """
        }
    }
}

final class CursorThemeController: NSObject {
    static let shared = CursorThemeController()

    private static let systemThemeID = "__system__"
    private static let selectedThemeKey = "SelectedCursorTheme"
    private static let followActionsKey = "CursorFollowsPetActions"
    private static let mousecapeBundleIdentifier = "com.alexzielenski.Mousecape"
    private static let downloadURL = URL(string: "https://github.com/alexzielenski/Mousecape/releases")!

    private let workerQueue = DispatchQueue(label: "io.insiderx.desktop-pet-engine.cursor-theme")
    private let fileManager = FileManager.default
    private let themesDirectory: URL?
    private let themes: [CursorThemeDefinition]
    private let configurationError: Error?

    private(set) var selectedThemeID: String
    private(set) var followsPetActions: Bool

    private override init() {
        themesDirectory = Self.resolveThemesDirectory()

        do {
            themes = try Self.loadThemes(from: themesDirectory)
            configurationError = nil
        } catch {
            themes = []
            configurationError = error
        }

        let storedThemeID = UserDefaults.standard.string(forKey: Self.selectedThemeKey)
        if let storedThemeID,
           storedThemeID == Self.systemThemeID || themes.contains(where: { $0.id == storedThemeID }) {
            selectedThemeID = storedThemeID
        } else {
            selectedThemeID = Self.systemThemeID
        }

        followsPetActions = UserDefaults.standard.bool(forKey: Self.followActionsKey)
        super.init()
    }

    func makeMenuItem() -> NSMenuItem {
        let rootItem = NSMenuItem(title: "鼠标样式 / Cursor", action: nil, keyEquivalent: "")
        let submenu = NSMenu(title: rootItem.title)

        let systemItem = NSMenuItem(
            title: "系统默认 / System Default",
            action: #selector(selectTheme(_:)),
            keyEquivalent: ""
        )
        systemItem.target = self
        systemItem.representedObject = Self.systemThemeID
        systemItem.state = selectedThemeID == Self.systemThemeID ? .on : .off
        submenu.addItem(systemItem)

        for theme in themes {
            let item = NSMenuItem(
                title: theme.title.localized,
                action: #selector(selectTheme(_:)),
                keyEquivalent: ""
            )
            item.target = self
            item.representedObject = theme.id
            item.state = selectedThemeID == theme.id ? .on : .off
            submenu.addItem(item)
        }

        if let configurationError {
            let item = NSMenuItem(
                title: "配置无效 / Invalid Configuration",
                action: #selector(showConfigurationError),
                keyEquivalent: ""
            )
            item.target = self
            item.toolTip = configurationError.localizedDescription
            submenu.addItem(item)
        } else if themes.isEmpty {
            let item = NSMenuItem(
                title: "未配置自定义主题 / No Custom Themes",
                action: nil,
                keyEquivalent: ""
            )
            item.isEnabled = false
            submenu.addItem(item)
        }

        submenu.addItem(.separator())
        let followItem = NSMenuItem(
            title: "跟随宠物动作 / Follow Pet Actions",
            action: #selector(toggleFollowActions),
            keyEquivalent: ""
        )
        followItem.target = self
        followItem.state = followsPetActions ? .on : .off
        followItem.isEnabled = themes.contains { !($0.actions ?? []).isEmpty }
        submenu.addItem(followItem)

        submenu.addItem(.separator())
        let openItem = NSMenuItem(
            title: "打开 Mousecape / Open Mousecape",
            action: #selector(openMousecape),
            keyEquivalent: ""
        )
        openItem.target = self
        submenu.addItem(openItem)

        rootItem.submenu = submenu
        return rootItem
    }

    func restorePersistedThemeOnLaunch() {
        guard !isTestRun, selectedThemeID != Self.systemThemeID else { return }
        enqueueApply(selectedThemeID, reportErrors: true)
    }

    func petDidStart(action: PetAction) {
        guard followsPetActions, !isTestRun else { return }
        let actionThemeID = themes.first {
            ($0.actions ?? []).contains(action.rawValue)
        }?.id
        enqueueApply(actionThemeID ?? selectedThemeID, reportErrors: false)
    }

    func petDidEnterIdle() {
        guard followsPetActions, !isTestRun else { return }
        enqueueApply(selectedThemeID, reportErrors: false)
    }

    func restoreBaseThemeBeforeExit() {
        guard followsPetActions, !isTestRun else { return }
        let themeID = selectedThemeID
        workerQueue.sync {
            try? applyNow(themeID: themeID)
        }
    }

    @discardableResult
    func validateConfiguredThemes() throws -> Int {
        if let configurationError {
            throw configurationError
        }
        return try Self.loadThemes(from: themesDirectory).count
    }

    @objc private func selectTheme(_ sender: NSMenuItem) {
        guard let themeID = sender.representedObject as? String,
              themeID == Self.systemThemeID || themes.contains(where: { $0.id == themeID }) else {
            return
        }
        selectedThemeID = themeID
        UserDefaults.standard.set(themeID, forKey: Self.selectedThemeKey)
        NotificationCenter.default.post(name: .cursorThemeDidChange, object: themeID)
        enqueueApply(themeID, reportErrors: true)
    }

    @objc private func toggleFollowActions() {
        followsPetActions.toggle()
        UserDefaults.standard.set(followsPetActions, forKey: Self.followActionsKey)
        NotificationCenter.default.post(name: .cursorThemeDidChange, object: followsPetActions)
        enqueueApply(selectedThemeID, reportErrors: true)
    }

    @objc private func openMousecape() {
        if let appURL = mousecapeApplicationURL() {
            NSWorkspace.shared.openApplication(
                at: appURL,
                configuration: NSWorkspace.OpenConfiguration()
            )
            return
        }
        presentMousecapeMissingAlert()
    }

    @objc private func showConfigurationError() {
        guard let configurationError else { return }
        presentApplyError(configurationError)
    }

    private var isTestRun: Bool {
        CommandLine.arguments.contains("--self-test")
            || CommandLine.arguments.contains("--cursor-self-test")
            || CommandLine.arguments.contains("--animation-smoke-test")
    }

    private func enqueueApply(_ themeID: String, reportErrors: Bool) {
        workerQueue.async { [weak self] in
            guard let self else { return }
            do {
                try self.applyNow(themeID: themeID)
            } catch {
                guard reportErrors else { return }
                DispatchQueue.main.async {
                    self.presentApplyError(error)
                }
            }
        }
    }

    private func applyNow(themeID: String) throws {
        let executableURL = try mousecloakExecutableURL()
        let arguments: [String]

        if themeID == Self.systemThemeID {
            arguments = ["--reset"]
        } else {
            guard let theme = themes.first(where: { $0.id == themeID }) else {
                throw CursorThemeError.invalidConfiguration("unknown theme \(themeID)")
            }
            let sourceURL = try Self.validatedCapeURL(for: theme, in: themesDirectory)
            let installedURL = try installCape(sourceURL, identifier: theme.capeIdentifier)
            arguments = ["--apply", installedURL.path]
        }

        let process = Process()
        let outputPipe = Pipe()
        process.executableURL = executableURL
        process.arguments = arguments
        process.standardOutput = outputPipe
        process.standardError = outputPipe

        do {
            try process.run()
        } catch {
            throw CursorThemeError.mousecloakFailed(error.localizedDescription)
        }

        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        let output = String(data: outputData, encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let normalizedOutput = output.lowercased()
        if process.terminationStatus != 0
            || normalizedOutput.contains("failed")
            || normalizedOutput.contains("could not")
            || normalizedOutput.contains("invalid") {
            let details = output.isEmpty
                ? "mousecloak exited with status \(process.terminationStatus)"
                : output
            throw CursorThemeError.mousecloakFailed(details)
        }
    }

    private func installCape(_ sourceURL: URL, identifier: String) throws -> URL {
        let capesDirectory = fileManager.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Mousecape/capes", isDirectory: true)
        try fileManager.createDirectory(
            at: capesDirectory,
            withIntermediateDirectories: true,
            attributes: nil
        )

        let destinationURL = capesDirectory
            .appendingPathComponent(identifier)
            .appendingPathExtension("cape")
        try Data(contentsOf: sourceURL).write(to: destinationURL, options: .atomic)
        return destinationURL
    }

    private func mousecloakExecutableURL() throws -> URL {
        guard let applicationURL = mousecapeApplicationURL() else {
            throw CursorThemeError.mousecapeMissing
        }
        return applicationURL.appendingPathComponent("Contents/MacOS/mousecloak")
    }

    private func mousecapeApplicationURL() -> URL? {
        var candidates: [URL] = []
        if let registeredURL = NSWorkspace.shared.urlForApplication(
            withBundleIdentifier: Self.mousecapeBundleIdentifier
        ) {
            candidates.append(registeredURL)
        }
        candidates.append(
            fileManager.homeDirectoryForCurrentUser
                .appendingPathComponent("Applications/Mousecape.app")
        )
        candidates.append(URL(fileURLWithPath: "/Applications/Mousecape.app"))

        return candidates.first { candidate in
            guard Bundle(url: candidate)?.bundleIdentifier == Self.mousecapeBundleIdentifier else {
                return false
            }
            return fileManager.isExecutableFile(
                atPath: candidate.appendingPathComponent("Contents/MacOS/mousecloak").path
            )
        }
    }

    private func presentApplyError(_ error: Error) {
        if case CursorThemeError.mousecapeMissing = error {
            presentMousecapeMissingAlert()
            return
        }

        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = "无法切换鼠标样式 / Could Not Change Cursor"
        alert.informativeText = error.localizedDescription
        alert.addButton(withTitle: "好 / OK")
        alert.runModal()
    }

    private func presentMousecapeMissingAlert() {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = "需要安装 Mousecape / Mousecape Is Required"
        alert.informativeText = CursorThemeError.mousecapeMissing.localizedDescription
        alert.addButton(withTitle: "打开下载页 / Open Download Page")
        alert.addButton(withTitle: "取消 / Cancel")
        if alert.runModal() == .alertFirstButtonReturn {
            NSWorkspace.shared.open(Self.downloadURL)
        }
    }

    private static func resolveThemesDirectory() -> URL? {
        if let override = ProcessInfo.processInfo.environment["DESKTOP_PET_CURSOR_THEMES_DIR"],
           !override.isEmpty {
            return URL(fileURLWithPath: override, isDirectory: true)
        }
        return Bundle.main.resourceURL?
            .appendingPathComponent("CursorThemes", isDirectory: true)
    }

    private static func loadThemes(from directory: URL?) throws -> [CursorThemeDefinition] {
        guard let directory else { return [] }
        let manifestURL = directory.appendingPathComponent("manifest.json")
        guard FileManager.default.fileExists(atPath: manifestURL.path) else { return [] }

        let manifest = try JSONDecoder().decode(
            CursorThemeManifest.self,
            from: Data(contentsOf: manifestURL)
        )
        guard manifest.version == 1 else {
            throw CursorThemeError.unsupportedManifestVersion(manifest.version)
        }

        var ids = Set<String>()
        var capeIdentifiers = Set<String>()
        let validActions = Set(PetAction.allCases.map(\.rawValue))

        for theme in manifest.themes {
            guard isSafeIdentifier(theme.id) else {
                throw CursorThemeError.invalidConfiguration("unsafe theme id \(theme.id)")
            }
            guard ids.insert(theme.id).inserted else {
                throw CursorThemeError.invalidConfiguration("duplicate theme id \(theme.id)")
            }
            guard isSafeIdentifier(theme.capeIdentifier) else {
                throw CursorThemeError.invalidConfiguration(
                    "unsafe cape identifier \(theme.capeIdentifier)"
                )
            }
            guard capeIdentifiers.insert(theme.capeIdentifier).inserted else {
                throw CursorThemeError.invalidConfiguration(
                    "duplicate cape identifier \(theme.capeIdentifier)"
                )
            }
            guard !theme.title.english.isEmpty, !theme.title.simplifiedChinese.isEmpty else {
                throw CursorThemeError.invalidConfiguration("empty title for \(theme.id)")
            }
            let fileURL = URL(fileURLWithPath: theme.capeFile)
            guard fileURL.lastPathComponent == theme.capeFile,
                  fileURL.pathExtension.lowercased() == "cape" else {
                throw CursorThemeError.invalidConfiguration(
                    "unsafe cape filename \(theme.capeFile)"
                )
            }
            for action in theme.actions ?? [] where !validActions.contains(action) {
                throw CursorThemeError.invalidConfiguration(
                    "unknown action \(action) in \(theme.id)"
                )
            }
            _ = try validatedCapeURL(for: theme, in: directory)
        }

        return manifest.themes
    }

    private static func validatedCapeURL(
        for theme: CursorThemeDefinition,
        in directory: URL?
    ) throws -> URL {
        guard let directory else {
            throw CursorThemeError.bundledCapeMissing(theme.capeFile)
        }
        let resourceURL = directory.appendingPathComponent(theme.capeFile)
        guard FileManager.default.fileExists(atPath: resourceURL.path) else {
            throw CursorThemeError.bundledCapeMissing(theme.capeFile)
        }

        let propertyList = try PropertyListSerialization.propertyList(
            from: Data(contentsOf: resourceURL),
            options: [],
            format: nil
        )
        guard let dictionary = propertyList as? [String: Any],
              dictionary["Identifier"] as? String == theme.capeIdentifier else {
            throw CursorThemeError.invalidCape(theme.capeFile)
        }
        return resourceURL
    }

    private static func isSafeIdentifier(_ value: String) -> Bool {
        guard !value.isEmpty, value.count <= 128, !value.contains("..") else { return false }
        let allowed = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        return value.unicodeScalars.allSatisfy { allowed.contains($0) }
    }
}

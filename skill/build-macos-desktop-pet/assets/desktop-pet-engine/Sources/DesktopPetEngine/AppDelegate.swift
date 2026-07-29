import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var window: PetWindow?
    private var controller: PetController?
    private var statusItem: NSStatusItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(cursorThemeDidChange),
            name: .cursorThemeDidChange,
            object: nil
        )

        do {
            let assets = try AssetCatalog()
            try assets.validateRequiredAssets()

            let petWindow = PetWindow(sideLength: PetSize.medium.sideLength)
            let petView = PetView(frame: NSRect(origin: .zero, size: petWindow.frame.size))
            petView.autoresizingMask = [.width, .height]
            petWindow.contentView = petView

            if let screen = NSScreen.main {
                let visible = screen.visibleFrame
                petWindow.setFrameOrigin(NSPoint(
                    x: visible.maxX - petWindow.frame.width - 24,
                    y: visible.minY + 24
                ))
            }

            let petController = PetController(window: petWindow, view: petView, assets: assets)
            petView.controller = petController
            window = petWindow
            controller = petController

            installStatusItem()
            petWindow.orderFrontRegardless()
            petController.start()
        } catch {
            presentFatalError(error)
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        CursorThemeController.shared.restoreBaseThemeBeforeExit()
        NotificationCenter.default.removeObserver(self)
        window?.ignoresMouseEvents = true
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        controller?.showPet()
        return true
    }

    func applicationDockMenu(_ sender: NSApplication) -> NSMenu? {
        let menu = NSMenu(title: "桌宠引擎")

        let showItem = NSMenuItem(title: "显示示例桌宠", action: #selector(showPet), keyEquivalent: "")
        showItem.target = self
        menu.addItem(showItem)

        let hideItem = NSMenuItem(title: "隐藏示例桌宠", action: #selector(hidePet), keyEquivalent: "")
        hideItem.target = self
        menu.addItem(hideItem)

        menu.addItem(CursorThemeController.shared.makeMenuItem())

        menu.addItem(.separator())
        let quitItem = NSMenuItem(title: "退出", action: #selector(quitApp), keyEquivalent: "")
        quitItem.target = self
        menu.addItem(quitItem)
        return menu
    }

    private func installStatusItem() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        item.button?.title = "🐾"
        item.button?.toolTip = "桌宠引擎"
        statusItem = item
        rebuildStatusMenu()
    }

    private func rebuildStatusMenu() {
        guard let item = statusItem else { return }
        let menu = NSMenu(title: "桌宠引擎")
        let showItem = NSMenuItem(title: "显示示例桌宠", action: #selector(showPet), keyEquivalent: "")
        showItem.target = self
        menu.addItem(showItem)

        let hideItem = NSMenuItem(title: "隐藏示例桌宠", action: #selector(hidePet), keyEquivalent: "")
        hideItem.target = self
        menu.addItem(hideItem)

        menu.addItem(CursorThemeController.shared.makeMenuItem())

        menu.addItem(.separator())
        let quitItem = NSMenuItem(title: "退出", action: #selector(quitApp), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        item.menu = menu
    }

    @objc private func showPet() {
        controller?.showPet()
    }

    @objc private func hidePet() {
        controller?.hidePet()
    }

    @objc private func cursorThemeDidChange() {
        DispatchQueue.main.async { [weak self] in
            self?.rebuildStatusMenu()
        }
    }

    @objc private func quitApp() {
        NSApp.terminate(nil)
    }

    private func presentFatalError(_ error: Error) {
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = "桌宠引擎无法启动"
        alert.informativeText = error.localizedDescription
        alert.addButton(withTitle: "退出")
        alert.runModal()
        NSApp.terminate(nil)
    }
}
